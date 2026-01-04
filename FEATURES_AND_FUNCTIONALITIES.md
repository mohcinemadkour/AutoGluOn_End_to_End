# 📋 AutoGluon Churn Prediction - Complete Features & Functionalities

**Project:** Enterprise-Grade Customer Churn Prediction System  
**Last Updated:** January 3, 2026  
**Version:** 1.0 (Secure Edition)

---

## 🎯 Project Overview

A production-ready machine learning system for predicting customer churn using AutoGluon AutoML, featuring comprehensive security, real-time predictions, interactive dashboards, and enterprise data integration.

---

## 🏗️ System Architecture

### **Core Components**

1. **Machine Learning Engine** - AutoGluon AutoML with hyperparameter optimization
2. **REST API** - FastAPI-based prediction service
3. **Interactive Dashboard** - Streamlit-based business intelligence interface
4. **Data Pipeline** - Automated data extraction, validation, and quality monitoring
5. **Security Layer** - JWT authentication, RBAC, and audit logging
6. **Database Integration** - SingleStore/MySQL database connector
7. **Monitoring System** - Data quality tracking and metrics collection

---

## 🚀 Core Features

### 1. **Machine Learning Capabilities**

#### **AutoML Training & Optimization**
- **AutoGluon TabularPredictor**: State-of-the-art automated machine learning
  - Automatic feature engineering
  - Ensemble model selection
  - Cross-validation and stacking
  - Model persistence and versioning

- **Hyperparameter Optimization (HPO)**:
  - Optuna-based hyperparameter tuning
  - Multi-objective optimization
  - Configurable search spaces
  - Best model selection and export
  - Results visualization and analysis

- **Custom Metrics**:
  - Business-weighted F1 score
  - Cost-sensitive evaluation
  - Recall@precision thresholds
  - ROC-AUC and PR-AUC

#### **Model Management**
- Model versioning and metadata tracking
- Automatic model loading and validation
- Performance leaderboard
- Feature importance analysis
- Model export/import capabilities

**Key Files:**
- [run_autogluon.py](run_autogluon.py) - Training orchestration
- [custom_metrics.py](custom_metrics.py) - Custom evaluation metrics
- [autogluon_config.yaml](autogluon_config.yaml) - Training configuration
- `autogluon_churn_model_hpo/` - Trained model artifacts

---

### 2. **Prediction Services**

#### **REST API (FastAPI)**
**Base URL:** `http://localhost:8000`

**Endpoints:**

| Endpoint | Method | Auth Required | Rate Limit | Description |
|----------|--------|---------------|------------|-------------|
| `/` | GET | No | - | API information |
| `/health` | GET | No | - | Health check |
| `/token` | POST | No | - | Get JWT token |
| `/login` | POST | No | - | User authentication |
| `/predict` | POST | Yes (Viewer+) | 100/minute | Single prediction |
| `/predict_batch` | POST | Yes (Analyst+) | 20/minute | Batch predictions |
| `/model_info` | GET | Yes (Viewer+) | 50/minute | Model metadata |
| `/feature_importance` | GET | Yes (Analyst+) | 30/minute | Feature importance |
| `/users/me` | GET | Yes | 100/minute | Current user info |
| `/users` | POST | Yes (Admin) | 10/minute | Create user |
| `/users/list` | GET | Yes (Admin) | 50/minute | List users |
| `/users/{username}/role` | PUT | Yes (Admin) | 20/minute | Update user role |
| `/users/{username}` | DELETE | Yes (Admin) | 10/minute | Delete user |

**Features:**
- JWT token-based authentication
- Role-based access control (RBAC)
- API rate limiting (SlowAPI)
- Automatic data validation (Pydantic)
- Comprehensive error handling
- Audit logging for all operations
- Interactive documentation (Swagger UI at `/docs`)
- Alternative docs (ReDoc at `/redoc`)

**Key Files:**
- [app.py](app.py) - FastAPI application (618 lines)

---

### 3. **Interactive Dashboard**

#### **Streamlit Business Intelligence Dashboard**
**URL:** `http://localhost:8501`

**Pages & Features:**

##### **📊 Overview Page**
- Key performance metrics (total customers, at-risk count, churn rate)
- Real-time statistics dashboard
- Churn distribution visualizations
- Risk level breakdown
- Trend analysis

##### **🎯 Single Prediction Page**
- Interactive customer data input form
- Real-time churn probability prediction
- Risk level classification (Low/Medium/High/Critical)
- Confidence indicators
- Retention recommendations
- What-if scenario testing

##### **📦 Batch Predictions Page**
- CSV file upload for bulk predictions
- Automated batch processing
- Results visualization
- Export predictions as CSV
- Batch statistics and summaries

##### **📈 Model Performance Page**
- Model leaderboard comparison
- Feature importance charts
- Performance metrics (accuracy, precision, recall, F1)
- Confusion matrix
- ROC and PR curves
- Training history

##### **📊 Data Quality Page** (Admin Only)
- Data quality metrics over time
- Missing value analysis
- Outlier detection
- Data distribution charts
- Quality score tracking
- Validation results

##### **🔧 System Settings Page** (Admin Only)
- User management interface
- Role assignment
- Security configuration
- System health monitoring
- Audit log viewer

**Security Features:**
- Session-based authentication
- Role-based page access control
- Automatic session timeout
- Login/logout functionality
- Secure password handling
- Audit logging

**Key Files:**
- [dashboard.py](dashboard.py) - Main dashboard (911 lines)

---

### 4. **Security & Authentication**

#### **Authentication System**
- **JWT Token-Based Auth**: Secure API access with Bearer tokens
- **Session Management**: Streamlit session authentication
- **Password Security**: Bcrypt hashing with salt
- **Token Expiration**: Configurable access token lifetime (30 minutes default)

#### **Role-Based Access Control (RBAC)**

| Role | Permissions | Use Case |
|------|-------------|----------|
| **Admin** | Full system access, user management, system configuration | System administrators |
| **Analyst** | Predictions, batch processing, model info, data analysis | Data analysts, ML engineers |
| **Viewer** | Single predictions, view dashboards (read-only) | Business users, stakeholders |

#### **Default User Accounts**

| Username | Password | Role | Full Name |
|----------|----------|------|-----------|
| admin | admin123 | Admin | System Administrator |
| analyst | analyst123 | Analyst | Data Analyst |
| viewer | viewer123 | Viewer | Business Viewer |

⚠️ **Security Note:** Change default passwords in production!

#### **Security Features**
- Password complexity validation
- Account lockout after failed attempts
- Rate limiting on all endpoints
- CORS protection
- SQL injection prevention
- XSS protection
- Audit logging of all actions

**Key Files:**
- [auth/authentication.py](auth/authentication.py) - Auth manager
- [auth/audit_log.py](auth/audit_log.py) - Audit logging
- [config/security.yaml](config/security.yaml) - Security configuration

---

### 5. **Data Integration & Management**

#### **Database Connection**
- **SingleStore/MySQL Integration**: Production-ready database connector
- **Connection Pooling**: Efficient connection management
- **Auto-Reconnection**: Automatic connection recovery
- **Query Optimization**: Parameterized queries for performance

#### **Data Extraction**
- **CustomerDataExtractor**: Extracts customer features from database
  - Join queries across multiple tables
  - Feature aggregation
  - Date-based filtering
  - Batch extraction support

**Available Tables:**
- `customers` - Customer demographics
- `contracts` - Contract information
- `billing` - Billing history
- `payment_methods` - Payment details
- `service_calls` - Support tickets
- `churn_history` - Historical churn data

#### **Data Validation**
- **Schema Validation**: Type checking, required fields
- **Business Rules**: Value range validation, logical constraints
- **Data Quality Checks**: Missing values, outliers, duplicates
- **Automated Reports**: Quality score calculation

#### **Data Pipeline Features**
- Automated data refresh jobs
- Incremental updates
- Data versioning
- Quality monitoring
- Error handling and recovery

**Key Files:**
- [data/database.py](data/database.py) - Database connector (281 lines)
- [data/extractors.py](data/extractors.py) - Data extraction queries
- [data/validators.py](data/validators.py) - Validation rules
- [jobs/data_refresh.py](jobs/data_refresh.py) - Automated refresh jobs

---

### 6. **Monitoring & Quality Assurance**

#### **Data Quality Monitoring**
- **Metric Collection**:
  - Row/column counts
  - Missing value statistics
  - Duplicate detection
  - Data type consistency
  - Outlier detection
  - Distribution analysis

- **Quality Scoring**:
  - Overall quality score (0-100)
  - Per-column quality metrics
  - Trend tracking over time
  - Alerting for quality drops

- **Historical Tracking**:
  - JSON metrics storage
  - Time-series analysis
  - Quality degradation detection
  - Comparative reporting

#### **System Health Monitoring**
- API health checks
- Model loading status
- Database connectivity
- Memory usage tracking
- Response time monitoring

**Key Files:**
- [monitoring/data_quality.py](monitoring/data_quality.py) - Quality monitoring (369 lines)
- `monitoring/data_quality_metrics/` - Metrics storage

---

### 7. **Configuration Management**

#### **Configuration Files**

| File | Purpose | Format |
|------|---------|--------|
| `.env` | Environment variables, secrets | ENV |
| `autogluon_config.yaml` | AutoGluon training config | YAML |
| `config/security.yaml` | Security settings | YAML |
| `config/database.env.template` | Database config template | ENV |
| `my_new_config.yaml` | Custom training config | YAML |

#### **Environment Variables**
```
# Database
SINGLESTORE_HOST=localhost
SINGLESTORE_PORT=3306
SINGLESTORE_DATABASE=churn_db
SINGLESTORE_USER=admin
SINGLESTORE_PASSWORD=secret

# Security
JWT_SECRET_KEY=<generated>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API
API_RATE_LIMIT_PER_MINUTE=100
```

---

### 8. **Testing & Validation**

#### **Test Suites**

| Test File | Coverage | Tests |
|-----------|----------|-------|
| [test_api.py](test_api.py) | API endpoints | 4+ tests |
| [test_security.py](test_security.py) | Authentication, RBAC | 6+ tests |
| [test_extraction.py](test_extraction.py) | Data extraction | Multiple tests |
| [test_dashboard_data.py](test_dashboard_data.py) | Dashboard data | Integration tests |

#### **Test Coverage**
- Authentication flow
- JWT token generation/validation
- Role-based access control
- API endpoint functionality
- Database connectivity
- Data extraction accuracy
- Prediction consistency
- Audit logging

---

### 9. **Deployment Options**

#### **Local Development**
```bash
# Terminal 1: API
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Dashboard
streamlit run dashboard.py
```

#### **Docker Deployment**
```bash
docker-compose up
```
- Multi-container setup
- Automated builds
- Port mapping
- Volume mounts

#### **Cloud Deployment (Render.com)**
- Configured with `render.yaml`
- Automated deployments from Git
- Environment variable management
- Health check endpoints
- Scaling options

**Key Files:**
- [Dockerfile](Dockerfile) - Container definition
- [docker-compose.yml](docker-compose.yml) - Multi-container setup
- [render.yaml](render.yaml) - Render.com config
- [setup_render.py](setup_render.py) - Render deployment setup

---

### 10. **Synthetic Data Generation**

For testing and demonstration purposes:

#### **Data Generation Features**
- Realistic customer profiles
- Contract variations
- Billing patterns
- Service call history
- Churn patterns
- Statistical distributions

#### **Generated Tables**
- 1000+ synthetic customers
- Complete relationship mapping
- JSON and CSV formats
- SQL insert statements

**Key Files:**
- [setup_singlestore_synthetic.py](setup_singlestore_synthetic.py) - Data generator
- [schema.sql](schema.sql) - Database schema
- [insert_data.sql](insert_data.sql) - Sample data inserts
- `synthetic_data/` - Generated datasets
- `synthetic_data_new/` - Additional datasets

---

## 🔧 Utility Scripts

| Script | Purpose |
|--------|---------|
| [setup_security.py](setup_security.py) | Initialize security system |
| [setup_render.py](setup_render.py) | Prepare Render deployment |
| [regen_config.py](regen_config.py) | Regenerate configuration files |
| [add_more_data.py](add_more_data.py) | Add synthetic data |
| [simulate_data_refresh.py](simulate_data_refresh.py) | Test data refresh |

---

## 📊 Model Artifacts

### **Trained Models**
- `autogluon_baseline/` - Baseline model
- `autogluon_churn_model/` - Initial trained model
- `autogluon_churn_model_hpo/` - HPO-optimized model (active)

### **HPO Results**
- Best hyperparameters (JSON/YAML)
- Trial analysis reports
- Performance visualizations
- Retraining configurations

**Files:**
- `best_hpo_hyperparameters_*.json`
- `best_hpo_hyperparameters_*.yaml`
- `hpo_best_model_report_*.txt`
- `retrain_config_best_hpo_*.yaml`
- `feature_importance.png`
- `hpo_trial_analysis_comprehensive.png`
- `hpo_trial_heatmap.png`

---

## 📚 Documentation

### **Available Documentation**

| Document | Content |
|----------|---------|
| [README.md](README.md) | Main project documentation (431 lines) |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture (610 lines) |
| [SECURITY.md](SECURITY.md) | Security guidelines |
| [SECURITY_IMPLEMENTATION.md](SECURITY_IMPLEMENTATION.md) | Security implementation details |
| [AUTHENTICATION_SECURITY_IMPLEMENTATION.md](AUTHENTICATION_SECURITY_IMPLEMENTATION.md) | Auth implementation |
| [DATA_INTEGRATION_GUIDE.md](DATA_INTEGRATION_GUIDE.md) | Data integration instructions |
| [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) | Code examples and tutorials |
| [TESTING_DATA_REFRESH.md](TESTING_DATA_REFRESH.md) | Data refresh testing |
| [README_DASHBOARD.md](README_DASHBOARD.md) | Dashboard user guide |
| [README_DEPLOYMENT.md](README_DEPLOYMENT.md) | Deployment instructions |
| [README_RENDER_DEPLOYMENT.md](README_RENDER_DEPLOYMENT.md) | Render-specific deployment |
| [DEPLOY_GUIDE.md](DEPLOY_GUIDE.md) | General deployment guide |
| [NEXT.md](NEXT.md) | Future roadmap (508 lines) |

---

## 🎨 Visualization Features

### **Dashboard Visualizations**
- Churn distribution charts (pie, bar)
- Risk level breakdowns
- Time series analysis
- Feature importance plots
- Performance metrics dashboards
- Data quality trends

### **Model Analysis Visualizations**
- Confusion matrices
- ROC curves
- Precision-Recall curves
- Feature importance rankings
- HPO trial analysis
- Performance comparisons

---

## 🔐 Audit & Logging

### **Audit Logging System**
- **Event Types**: Login, logout, predictions, user management, data access
- **Log Storage**: `logs/audit/` directory
- **Format**: JSON with timestamps
- **Rotation**: Date-based file rotation
- **Retention**: Configurable retention policy

### **Application Logging**
- **Location**: `logs/app/` directory
- **Levels**: INFO, WARNING, ERROR, DEBUG
- **Format**: Structured logging with context
- **Rotation**: Size and time-based

---

## 📦 Dependencies

### **Core ML Libraries**
- `autogluon.tabular` - AutoML framework
- `scikit-learn` - Machine learning utilities
- `pandas` - Data manipulation
- `numpy` - Numerical computing

### **Web Frameworks**
- `fastapi` - REST API framework
- `uvicorn` - ASGI server
- `streamlit` - Dashboard framework

### **Security**
- `python-jose[cryptography]` - JWT tokens
- `passlib[bcrypt]` - Password hashing
- `slowapi` - Rate limiting

### **Database**
- `sqlalchemy` - ORM
- `pymysql` - MySQL connector
- `python-dotenv` - Environment management

### **Visualization**
- `plotly` - Interactive charts
- `matplotlib` - Static plots

**Full list:** [requirements.txt](requirements.txt)

---

## 🎯 Key Capabilities Summary

### **What This System Can Do:**

✅ **Predict Customer Churn** - Real-time and batch predictions with confidence scores  
✅ **Automate ML Training** - Hands-off model training with hyperparameter optimization  
✅ **Secure API Access** - JWT authentication with role-based permissions  
✅ **Interactive Analysis** - Business-friendly dashboard for non-technical users  
✅ **Data Integration** - Connect to production databases (SingleStore/MySQL)  
✅ **Quality Monitoring** - Automated data quality tracking and alerting  
✅ **Audit Compliance** - Complete audit trail of all system actions  
✅ **Flexible Deployment** - Local, Docker, or cloud deployment options  
✅ **User Management** - Multi-user support with granular access control  
✅ **Performance Tracking** - Model performance monitoring and comparison  
✅ **Batch Processing** - Efficient processing of large customer datasets  
✅ **Data Validation** - Automated validation and quality assurance  
✅ **Synthetic Testing** - Built-in synthetic data for development/testing  

---

## 📊 System Metrics

- **Total Python Files**: 20+
- **Total Lines of Code**: ~5000+
- **Documentation Files**: 13
- **Test Suites**: 4
- **API Endpoints**: 14+
- **Dashboard Pages**: 6
- **Security Roles**: 3
- **Database Tables**: 6+
- **Supported Users**: Unlimited

---

## 🌐 Integration Points

### **Input Sources**
- SingleStore/MySQL databases
- CSV file uploads
- REST API requests
- Direct function calls

### **Output Formats**
- JSON (API responses)
- CSV (batch exports)
- Interactive visualizations
- PDF reports (configurable)
- Audit logs (JSON)

### **External Services**
- Database servers (SingleStore/MySQL)
- Cloud platforms (Render.com)
- Container orchestration (Docker)
- Version control (GitHub)

---

## 🎓 User Personas

### **1. Business Analyst**
- Uses dashboard for insights
- Runs single predictions
- Views performance metrics
- Exports reports

### **2. Data Scientist**
- Trains new models
- Performs batch predictions
- Analyzes feature importance
- Monitors data quality

### **3. System Administrator**
- Manages users and roles
- Configures security settings
- Monitors system health
- Reviews audit logs

### **4. Application Developer**
- Integrates via REST API
- Implements authentication
- Handles predictions in apps
- Manages error scenarios

---

## 🔄 Data Flow

```
Database → Extraction → Validation → Quality Check → Model → Prediction → Dashboard/API
                                                                              ↓
                                                                         Audit Log
```

---

## 📞 Support Resources

- **Documentation**: See `docs/` folder and markdown files
- **Examples**: [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md)
- **Testing**: Run test suites in `test_*.py` files
- **Configuration**: Templates in `config/` folder
- **Logs**: Check `logs/` directory for troubleshooting

---

**End of Features & Functionalities Documentation**

For next steps and future enhancements, see [NEXT_STEPS.md](NEXT_STEPS.md).
