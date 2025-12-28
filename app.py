# ============================================================================
# CHURN PREDICTION API - FastAPI Application
# ============================================================================
# This API serves the trained AutoGluon model for real-time predictions
# Endpoints: /predict (single), /predict_batch (multiple), /health

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Security, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from pathlib import Path
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from jose import JWTError, jwt
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# AutoGluon imports
from autogluon.tabular import TabularPredictor
from autogluon.core.metrics import make_scorer
from sklearn.metrics import precision_score, recall_score

# Import authentication modules
from auth.authentication import AuthManager, UserRole, User
from auth.audit_log import get_audit_logger, AuditEventType

# Import custom metrics (must be available for model unpickling)
from custom_metrics import calculate_business_f1

# Register custom metric in __main__ namespace for pickle compatibility
import sys
if hasattr(sys.modules.get('__main__'), '__dict__'):
    sys.modules['__main__'].calculate_business_f1 = calculate_business_f1

# ============================================================================
# CONFIGURATION
# ============================================================================
MODEL_PATH = "./autogluon_churn_model_hpo"  # Path to your trained model
MODEL_VERSION = "v1.0"  # Update this with each model release
CHURN_THRESHOLD = 0.5  # Default threshold (can be overridden per request)

# Authentication setup
auth_manager = AuthManager()
audit_logger = get_audit_logger()
security = HTTPBearer()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# INITIALIZE FASTAPI APP
# ============================================================================
app = FastAPI(
    title="Churn Prediction API",
    description="AutoGluon-powered customer churn prediction service with JWT authentication",
    version=MODEL_VERSION,
    docs_url="/docs",  # Swagger UI at /docs
    redoc_url="/redoc"  # ReDoc at /redoc
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ============================================================================
# AUTHENTICATION HELPERS
# ============================================================================

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> User:
    """
    Dependency to get current authenticated user from JWT token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        token_data = auth_manager.decode_token(token)
        
        if token_data is None or token_data.username is None:
            audit_logger.log_event(
                AuditEventType.INVALID_TOKEN,
                username="unknown",
                success=False,
                error_message="Invalid token"
            )
            raise credentials_exception
        
        user = auth_manager.get_user(token_data.username)
        if user is None:
            raise credentials_exception
        
        if user.disabled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled"
            )
        
        # Return User object (not UserInDB with password)
        return User(**user.dict())
    
    except JWTError:
        audit_logger.log_event(
            AuditEventType.INVALID_TOKEN,
            username="unknown",
            success=False,
            error_message="JWT decode error"
        )
        raise credentials_exception


def require_role(required_role: UserRole):
    """
    Dependency factory for role-based access control
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if not auth_manager.check_permission(current_user.role, required_role):
            audit_logger.log_unauthorized_access(
                username=current_user.username,
                resource=f"role_required:{required_role.value}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role.value}"
            )
        return current_user
    return role_checker

# ============================================================================
# LOAD MODEL ON STARTUP
# ============================================================================
predictor = None

@app.on_event("startup")
async def load_model():
    """Load the AutoGluon model when the API starts"""
    global predictor
    try:
        logger.info(f"Loading model from {MODEL_PATH}...")
        predictor = TabularPredictor.load(MODEL_PATH)
        logger.info(f"Model loaded successfully! Version: {MODEL_VERSION}")
        logger.info(f"Model evaluation metric: {predictor.eval_metric}")
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        raise

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str

class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str
    expires_in: int
    username: str
    role: str

class CustomerFeatures(BaseModel):
    """Input features for a single customer prediction"""
    tenure_months: float = Field(..., description="Customer tenure in months", ge=0)
    monthly_charges: float = Field(..., description="Monthly subscription charges", ge=0)
    total_charges: float = Field(..., description="Total charges to date", ge=0)
    service_calls: float = Field(..., description="Number of service calls", ge=0)
    contract_duration: str = Field(..., description="Contract type: Monthly, Yearly, Two-Year")
    paperless_billing: float = Field(..., description="Paperless billing indicator")
    tech_support: float = Field(..., description="Tech support indicator")
    online_backup: float = Field(..., description="Online backup indicator")
    payment_method: str = Field(..., description="Payment method: Electronic, Credit Card, Bank Transfer, Mailed Check")
    internet_service: float = Field(..., description="Internet service indicator")
    streaming_tv: float = Field(..., description="Streaming TV indicator")
    streaming_movies: float = Field(..., description="Streaming movies indicator")
    device_protection: float = Field(..., description="Device protection indicator")
    online_security: float = Field(..., description="Online security indicator")
    senior_citizen: float = Field(..., description="Senior citizen indicator")
    
    class Config:
        schema_extra = {
            "example": {
                "tenure_months": 24.5,
                "monthly_charges": 65.50,
                "total_charges": 1572.00,
                "service_calls": 2.0,
                "contract_duration": "Two-Year",
                "paperless_billing": 1.2,
                "tech_support": 0.9,
                "online_backup": 0.3,
                "payment_method": "Credit Card",
                "internet_service": 0.8,
                "streaming_tv": 0.5,
                "streaming_movies": 0.6,
                "device_protection": 0.2,
                "online_security": 0.7,
                "senior_citizen": 0.1
            }
        }

class PredictionRequest(BaseModel):
    """Request for single customer prediction"""
    customer_id: Optional[str] = Field(None, description="Optional customer identifier")
    features: CustomerFeatures
    threshold: Optional[float] = Field(CHURN_THRESHOLD, description="Custom prediction threshold", ge=0, le=1)

class BatchPredictionRequest(BaseModel):
    """Request for batch predictions"""
    customers: List[Dict] = Field(..., description="List of customer feature dictionaries")
    threshold: Optional[float] = Field(CHURN_THRESHOLD, description="Custom prediction threshold", ge=0, le=1)

class PredictionResponse(BaseModel):
    """Response for single prediction"""
    customer_id: Optional[str]
    churn_probability: float
    churn_prediction: str
    risk_level: str
    threshold_used: float
    model_version: str
    timestamp: str

class BatchPredictionResponse(BaseModel):
    """Response for batch predictions"""
    total_customers: int
    predictions: List[PredictionResponse]
    summary: Dict[str, int]
    model_version: str
    timestamp: str

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_risk_level(probability: float) -> str:
    """Categorize churn probability into risk levels"""
    if probability >= 0.7:
        return "HIGH"
    elif probability >= 0.4:
        return "MEDIUM"
    else:
        return "LOW"

def features_to_dataframe(features: CustomerFeatures) -> pd.DataFrame:
    """Convert CustomerFeatures to pandas DataFrame"""
    return pd.DataFrame([features.dict()])

def validate_model_loaded():
    """Check if model is loaded"""
    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please try again later."
        )

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/", tags=["General"])
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Churn Prediction API",
        "version": MODEL_VERSION,
        "status": "running",
        "model_loaded": predictor is not None,
        "authentication": "JWT token required",
        "endpoints": {
            "login": "/token",
            "predict": "/predict",
            "predict_batch": "/predict_batch",
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.post("/token", response_model=TokenResponse, tags=["Authentication"])
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login endpoint
    
    Returns JWT access token for authenticated users
    """
    user = auth_manager.authenticate_user(form_data.username, form_data.password)
    
    if not user:
        audit_logger.log_login(
            username=form_data.username,
            success=False,
            ip_address=request.client.host,
            error_message="Invalid credentials"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    from auth.authentication import create_access_token as create_token
    token = create_token(user.username, user.role, auth_manager)
    
    # Log successful login
    audit_logger.log_login(
        username=user.username,
        success=True,
        ip_address=request.client.host
    )
    
    return TokenResponse(
        access_token=token.access_token,
        token_type=token.token_type,
        expires_in=token.expires_in,
        username=user.username,
        role=user.role.value
    )

@app.post("/login", response_model=TokenResponse, tags=["Authentication"])
async def login_json(request: Request, login_data: LoginRequest):
    """
    Alternative JSON-based login endpoint
    
    Returns JWT access token for authenticated users
    """
    user = auth_manager.authenticate_user(login_data.username, login_data.password)
    
    if not user:
        audit_logger.log_login(
            username=login_data.username,
            success=False,
            ip_address=request.client.host,
            error_message="Invalid credentials"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Create access token
    from auth.authentication import create_access_token as create_token
    token = create_token(user.username, user.role, auth_manager)
    
    # Log successful login
    audit_logger.log_login(
        username=user.username,
        success=True,
        ip_address=request.client.host
    )
    
    return TokenResponse(
        access_token=token.access_token,
        token_type=token.token_type,
        expires_in=token.expires_in,
        username=user.username,
        role=user.role.value
    )

@app.get("/health", tags=["General"])
async def health_check():
    """Health check endpoint for monitoring (no authentication required)"""
    try:
        validate_model_loaded()
        return {
            "status": "healthy",
            "model_loaded": True,
            "model_path": MODEL_PATH,
            "model_version": MODEL_VERSION,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.post("/predict", response_model=PredictionResponse, tags=["Predictions"])
async def predict_single_customer(
    request_data: PredictionRequest,
    request: Request,
    current_user: User = Depends(require_role(UserRole.VIEWER))  # Minimum role: VIEWER
):
    """
    Predict churn for a single customer (requires authentication)
    
    Returns:
    - churn_probability: Probability of churn (0-1)
    - churn_prediction: Binary prediction (Yes/No)
    - risk_level: Risk category (HIGH/MEDIUM/LOW)
    """
    try:
        validate_model_loaded()
        
        # Convert features to DataFrame
        customer_df = features_to_dataframe(request_data.features)
        
        # Get prediction probabilities
        proba = predictor.predict_proba(customer_df)
        churn_prob = float(proba['Yes'].iloc[0])
        
        # Make binary prediction based on threshold
        churn_prediction = "Yes" if churn_prob >= request_data.threshold else "No"
        
        # Get risk level
        risk_level = get_risk_level(churn_prob)
        
        # Log prediction
        audit_logger.log_prediction(
            username=current_user.username,
            user_role=current_user.role.value,
            prediction_data={
                "customer_id": request_data.customer_id,
                "churn_probability": churn_prob,
                "risk_level": risk_level
            },
            success=True,
            ip_address=request.client.host
        )
        
        logger.info(f"Prediction for customer {request_data.customer_id} by {current_user.username}: {churn_prob:.3f}")
        
        return PredictionResponse(
            customer_id=request_data.customer_id,
            churn_probability=round(churn_prob, 4),
            churn_prediction=churn_prediction,
            risk_level=risk_level,
            threshold_used=request_data.threshold,
            model_version=MODEL_VERSION,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        audit_logger.log_prediction(
            username=current_user.username,
            user_role=current_user.role.value,
            prediction_data={"customer_id": request_data.customer_id},
            success=False,
            error_message=str(e),
            ip_address=request.client.host
        )
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.post("/predict_batch", response_model=BatchPredictionResponse, tags=["Predictions"])
async def predict_batch_customers(
    request_data: BatchPredictionRequest,
    request: Request,
    current_user: User = Depends(require_role(UserRole.ANALYST))  # Batch requires ANALYST role
):
    """
    Predict churn for multiple customers in batch (requires ANALYST role or higher)
    
    More efficient than calling /predict multiple times
    """
    try:
        validate_model_loaded()
        
        # Convert list of dicts to DataFrame
        customers_df = pd.DataFrame(request_data.customers)
        
        # Get predictions
        proba = predictor.predict_proba(customers_df)
        churn_probs = proba['Yes'].values
        
        # Create predictions list
        predictions = []
        risk_summary = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        churn_summary = {"Yes": 0, "No": 0}
        
        for i, prob in enumerate(churn_probs):
            churn_prediction = "Yes" if prob >= request_data.threshold else "No"
            risk_level = get_risk_level(prob)
            
            # Get customer_id if provided
            customer_id = request_data.customers[i].get('customer_id', f"customer_{i}")
            
            predictions.append(PredictionResponse(
                customer_id=customer_id,
                churn_probability=round(float(prob), 4),
                churn_prediction=churn_prediction,
                risk_level=risk_level,
                threshold_used=request.threshold,
                model_version=MODEL_VERSION,
                timestamp=datetime.now().isoformat()
            ))
            
            risk_summary[risk_level] += 1
            churn_summary[churn_prediction] += 1
        
        # Log batch prediction
        audit_logger.log_prediction(
            username=current_user.username,
            user_role=current_user.role.value,
            prediction_data={
                "batch_size": len(predictions),
                "high_risk": risk_summary["HIGH"],
                "medium_risk": risk_summary["MEDIUM"],
                "low_risk": risk_summary["LOW"]
            },
            success=True,
            ip_address=request.client.host
        )
        
        logger.info(f"Batch prediction completed for {len(customers_df)} customers by {current_user.username}")
        
        return BatchPredictionResponse(
            total_customers=len(predictions),
            predictions=predictions,
            summary={
                "high_risk": risk_summary["HIGH"],
                "medium_risk": risk_summary["MEDIUM"],
                "low_risk": risk_summary["LOW"],
                "predicted_churn": churn_summary["Yes"],
                "predicted_stay": churn_summary["No"]
            },
            model_version=MODEL_VERSION,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Batch prediction error: {str(e)}")
        audit_logger.log_prediction(
            username=current_user.username,
            user_role=current_user.role.value,
            prediction_data={"batch_size": len(request_data.customers)},
            success=False,
            error_message=str(e),
            ip_address=request.client.host
        )
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")

@app.get("/model_info", tags=["Model"])
async def get_model_info(current_user: User = Depends(get_current_user)):
    """Get information about the loaded model (requires authentication)"""
    try:
        validate_model_loaded()
        
        # Get model leaderboard
        leaderboard = predictor.leaderboard(silent=True)
        best_model = leaderboard.iloc[0]['model']
        best_score = leaderboard.iloc[0]['score_val']
        
        return {
            "model_version": MODEL_VERSION,
            "model_path": MODEL_PATH,
            "eval_metric": predictor.eval_metric.name,
            "best_model": best_model,
            "best_score": float(best_score),
            "total_models": len(leaderboard),
            "label": predictor.label,
            "problem_type": predictor.problem_type,
            "features": predictor.feature_metadata_in.get_features()
        }
        
    except Exception as e:
        logger.error(f"Model info error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")

# Admin endpoint for managing users
@app.get("/admin/users", tags=["Admin"])
async def list_users(current_user: User = Depends(require_role(UserRole.ADMIN))):
    """List all users (ADMIN only)"""
    return auth_manager.get_all_users()

@app.get("/admin/audit/stats", tags=["Admin"])
async def get_audit_stats(
    days: int = 7,
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Get audit log statistics (ADMIN only)"""
    return audit_logger.get_statistics(days=days)

# ============================================================================
# RUN THE API
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Run the API server
    uvicorn.run(
        "app:app",
        host="0.0.0.0",  # Listen on all network interfaces
        port=8000,        # Port to run on
        reload=True,      # Auto-reload on code changes (disable in production)
        log_level="info"
    )
