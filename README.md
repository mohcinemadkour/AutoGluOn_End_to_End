# 🔐 AutoGluon Churn Prediction - Secure Edition

Enterprise-grade customer churn prediction system with comprehensive authentication and security features.

## 🌟 Features

### Core ML Capabilities
- ✅ **AutoGluon AutoML** - State-of-the-art automated machine learning
- ✅ **Hyperparameter Optimization** - Model tuning with Optuna
- ✅ **Real-time Predictions** - Fast API for single customer predictions
- ✅ **Batch Processing** - Efficient batch prediction capabilities
- ✅ **Interactive Dashboard** - Streamlit-based business dashboard

### 🔒 Security Features (NEW!)
- ✅ **JWT Token Authentication** - Secure API access with Bearer tokens
- ✅ **Role-Based Access Control** - Admin, Analyst, and Viewer roles
- ✅ **API Rate Limiting** - Protection against abuse
- ✅ **Comprehensive Audit Logging** - Track all security events
- ✅ **Dashboard Authentication** - Protected Streamlit interface
- ✅ **Secure Configuration** - Environment variable management

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd AutoGluOn_End_to_End

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Security Setup

```bash
# Run automated security setup
python setup_security.py
```

This will:
- Create secure environment variables
- Generate JWT secret keys
- Set up audit log directories
- Display default credentials

### 3. Start Services

```bash
# Terminal 1: Start API
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start Dashboard
streamlit run dashboard.py
```

### 4. Login & Test

**Dashboard:** http://localhost:8501
- Username: `admin`
- Password: `admin123`

**API Docs:** http://localhost:8000/docs

## 📚 Documentation

- **[SECURITY.md](SECURITY.md)** - Complete security guide
- **[SECURITY_IMPLEMENTATION.md](SECURITY_IMPLEMENTATION.md)** - Implementation details
- **[auth/README.md](auth/README.md)** - Authentication module docs
- **[README_DASHBOARD.md](README_DASHBOARD.md)** - Dashboard guide
- **[README_DEPLOYMENT.md](README_DEPLOYMENT.md)** - Deployment guide

## 🔐 Default User Accounts

| Username | Password | Role | Permissions |
|----------|----------|------|-------------|
| admin | admin123 | Admin | Full access, user management |
| analyst | analyst123 | Analyst | Predictions, batch processing |
| viewer | viewer123 | Viewer | Read-only, single predictions |

**⚠️ IMPORTANT:** Change these passwords in production!

## 📡 API Usage

### 1. Get Authentication Token

```bash
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

### 2. Make Predictions

```bash
# Save token
TOKEN="your-jwt-token-here"

# Single prediction
curl -X POST "http://localhost:8000/predict" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "C12345",
    "features": {
      "tenure_months": 24,
      "monthly_charges": 65.50,
      "total_charges": 1572.00,
      "service_calls": 2,
      "contract_duration": "Monthly",
      "paperless_billing": 1,
      "tech_support": 0,
      "online_backup": 1,
      "payment_method": "Electronic",
      "internet_service": 1,
      "streaming_tv": 1,
      "streaming_movies": 0,
      "device_protection": 1,
      "online_security": 0,
      "senior_citizen": 0
    },
    "threshold": 0.5
  }'
```

## 🐍 Python Client Example

```python
import requests

# Login
response = requests.post(
    "http://localhost:8000/token",
    data={"username": "analyst", "password": "analyst123"}
)
token = response.json()["access_token"]

# Make prediction
headers = {"Authorization": f"Bearer {token}"}
response = requests.post(
    "http://localhost:8000/predict",
    headers=headers,
    json={
        "customer_id": "C12345",
        "features": {
            "tenure_months": 24,
            "monthly_charges": 65.50,
            # ... other features
        },
        "threshold": 0.5
    }
)

result = response.json()
print(f"Churn Probability: {result['churn_probability']:.2%}")
print(f"Risk Level: {result['risk_level']}")
```

## 🏗️ Project Structure

```
AutoGluOn_End_to_End/
├── auth/                           # Authentication module
│   ├── __init__.py
│   ├── authentication.py          # JWT, RBAC, user management
│   ├── audit_log.py               # Audit logging
│   └── README.md
├── config/
│   ├── database.env.template
│   └── security.yaml              # Security configuration
├── data/                          # Data extraction & validation
├── monitoring/                    # Data quality monitoring
├── logs/                          # Application & audit logs
│   └── audit/                     # Security audit logs
├── app.py                         # FastAPI application (secured)
├── dashboard.py                   # Streamlit dashboard (secured)
├── setup_security.py              # Security setup script
├── test_security.py               # Security test suite
├── .env.example                   # Environment template
├── requirements.txt               # Python dependencies
├── SECURITY.md                    # Security documentation
└── SECURITY_IMPLEMENTATION.md     # Implementation guide
```

## 🧪 Testing

### Run Security Tests

```bash
python test_security.py
```

Tests include:
- User authentication
- JWT token validation
- Role-based access control
- Audit logging
- Password hashing

### Test API

```bash
# Install httpie
pip install httpie

# Health check (no auth required)
http GET localhost:8000/health

# Login
http POST localhost:8000/login username=admin password=admin123

# Test with auth
http POST localhost:8000/predict Authorization:"Bearer <token>" < customer.json
```

## 🔒 Security Features

### Authentication
- JWT token-based authentication
- Bcrypt password hashing
- Token expiration (configurable)
- Secure session management

### Authorization
- Role-based access control (RBAC)
- Three-tier permission system
- Endpoint-level protection
- Resource-based access control

### Rate Limiting
- Per-endpoint limits
- IP-based tracking
- Configurable thresholds
- Automatic blocking

### Audit Logging
- All authentication events
- Prediction tracking
- Failed access attempts
- Admin actions
- Daily log rotation

### Configuration
- Environment variables
- Secure secret management
- YAML configuration
- Production-ready defaults

## 📊 Dashboard Features

### For All Users
- Customer overview
- Churn risk metrics
- Prediction interface
- Risk segmentation

### For Analysts & Admins
- Batch predictions
- Data export
- Analytics views
- Campaign planning

### For Admins Only
- User management
- Audit log viewing
- System configuration
- Access control

## 🚀 Deployment

### Development

```bash
# API
uvicorn app:app --reload

# Dashboard
streamlit run dashboard.py
```

### Production

```bash
# API with Gunicorn
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Dashboard
streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0
```

See [README_DEPLOYMENT.md](README_DEPLOYMENT.md) for detailed deployment instructions.

## 🔧 Configuration

### Environment Variables (.env)

```env
# JWT Authentication
JWT_SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Audit Logging
AUDIT_LOG_DIR=./logs/audit

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

### Security Configuration (config/security.yaml)

```yaml
roles:
  admin:
    permissions:
      - read
      - write
      - predict
      - batch_predict
      - manage_users
      
rate_limits:
  predict_single:
    requests: 30
    window: "1 minute"
```

## 📈 Monitoring

### Audit Logs

View logs in `logs/audit/audit_YYYY-MM-DD.jsonl`

```bash
# View today's logs
cat logs/audit/audit_$(date +%Y-%m-%d).jsonl | jq

# Count events by type
cat logs/audit/*.jsonl | jq -r '.event_type' | sort | uniq -c
```

### Admin Endpoints

```bash
# Get audit statistics (admin only)
http GET localhost:8000/admin/audit/stats?days=7 Authorization:"Bearer <token>"

# List users (admin only)
http GET localhost:8000/admin/users Authorization:"Bearer <token>"
```

## 🛠️ Development

### Add New User Role

```python
# In auth/authentication.py
class UserRole(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"
    DATA_SCIENTIST = "data_scientist"  # New role
```

### Add New Endpoint

```python
# In app.py
@app.get("/new_endpoint")
async def new_endpoint(
    current_user: User = Depends(require_role(UserRole.ANALYST))
):
    # Your logic here
    pass
```

### Custom Audit Event

```python
from auth.audit_log import get_audit_logger, AuditEventType

logger = get_audit_logger()
logger.log_event(AuditEvent(
    event_type=AuditEventType.DATA_EXPORTED,
    username=current_user.username,
    details={"export_type": "csv", "rows": 1000}
))
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see LICENSE file for details.

## ⚠️ Security Notice

This implementation includes demo credentials for ease of use. In production:

1. **Change all default passwords**
2. **Generate new secret keys**
3. **Enable HTTPS**
4. **Use database-backed user storage**
5. **Implement additional security measures**

See [SECURITY.md](SECURITY.md) for complete security guidelines.

## 📧 Support

- **Documentation:** Check the docs/ folder
- **Issues:** Open GitHub issue
- **Security:** Report privately (see SECURITY.md)

---

**Built with:** AutoGluon, FastAPI, Streamlit, JWT, and ❤️

**Version:** 1.0  
**Last Updated:** December 28, 2025
