# ============================================================================
# CHURN PREDICTION API - FastAPI Application
# ============================================================================
# This API serves the trained AutoGluon model for real-time predictions
# Endpoints: /predict (single), /predict_batch (multiple), /health

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from pathlib import Path

# AutoGluon imports
from autogluon.tabular import TabularPredictor
from autogluon.core.metrics import make_scorer
from sklearn.metrics import precision_score, recall_score

# ============================================================================
# CUSTOM METRIC FUNCTION (Must be defined before loading model)
# ============================================================================
def calculate_business_f1(y_true, y_pred, **kwargs):
    """
    Custom business F1 score function used during model training.
    This function must be defined before loading the model.
    """
    p = precision_score(y_true, y_pred, pos_label=1, zero_division=0)
    r = recall_score(y_true, y_pred, pos_label=1, zero_division=0)
    beta = 0.5  # Recall is beta-times more important
    if (beta**2 * p) + r == 0:
        return 0.0
    return (1 + beta**2) * (p * r) / ((beta**2 * p) + r)

# ============================================================================
# CONFIGURATION
# ============================================================================
MODEL_PATH = "./autogluon_churn_model_hpo"  # Path to your trained model
MODEL_VERSION = "v1.0"  # Update this with each model release
CHURN_THRESHOLD = 0.5  # Default threshold (can be overridden per request)

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
    description="AutoGluon-powered customer churn prediction service",
    version=MODEL_VERSION,
    docs_url="/docs",  # Swagger UI at /docs
    redoc_url="/redoc"  # ReDoc at /redoc
)

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
        "endpoints": {
            "predict": "/predict",
            "predict_batch": "/predict_batch",
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.get("/health", tags=["General"])
async def health_check():
    """Health check endpoint for monitoring"""
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
async def predict_single_customer(request: PredictionRequest):
    """
    Predict churn for a single customer
    
    Returns:
    - churn_probability: Probability of churn (0-1)
    - churn_prediction: Binary prediction (Yes/No)
    - risk_level: Risk category (HIGH/MEDIUM/LOW)
    """
    try:
        validate_model_loaded()
        
        # Convert features to DataFrame
        customer_df = features_to_dataframe(request.features)
        
        # Get prediction probabilities
        proba = predictor.predict_proba(customer_df)
        churn_prob = float(proba['Yes'].iloc[0])
        
        # Make binary prediction based on threshold
        churn_prediction = "Yes" if churn_prob >= request.threshold else "No"
        
        # Get risk level
        risk_level = get_risk_level(churn_prob)
        
        logger.info(f"Prediction for customer {request.customer_id}: {churn_prob:.3f}")
        
        return PredictionResponse(
            customer_id=request.customer_id,
            churn_probability=round(churn_prob, 4),
            churn_prediction=churn_prediction,
            risk_level=risk_level,
            threshold_used=request.threshold,
            model_version=MODEL_VERSION,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.post("/predict_batch", response_model=BatchPredictionResponse, tags=["Predictions"])
async def predict_batch_customers(request: BatchPredictionRequest):
    """
    Predict churn for multiple customers in batch
    
    More efficient than calling /predict multiple times
    """
    try:
        validate_model_loaded()
        
        # Convert list of dicts to DataFrame
        customers_df = pd.DataFrame(request.customers)
        
        # Get predictions
        proba = predictor.predict_proba(customers_df)
        churn_probs = proba['Yes'].values
        
        # Create predictions list
        predictions = []
        risk_summary = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        churn_summary = {"Yes": 0, "No": 0}
        
        for i, prob in enumerate(churn_probs):
            churn_prediction = "Yes" if prob >= request.threshold else "No"
            risk_level = get_risk_level(prob)
            
            # Get customer_id if provided
            customer_id = request.customers[i].get('customer_id', f"customer_{i}")
            
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
        
        logger.info(f"Batch prediction completed for {len(customers_df)} customers")
        
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
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")

@app.get("/model_info", tags=["Model"])
async def get_model_info():
    """Get information about the loaded model"""
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
