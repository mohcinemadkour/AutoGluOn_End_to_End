# Authentication & Security Guide

## Overview

This project implements comprehensive authentication and security features to protect sensitive customer data and predictions from unauthorized access.

## Security Features

### ✅ Implemented Features

1. **JWT Token-Based API Authentication**
   - Secure token-based authentication for all API endpoints
   - Token expiration and refresh mechanisms
   - Bearer token authorization

2. **Streamlit Dashboard Authentication**
   - User login system for dashboard access
   - Session management
   - Role-based UI customization

3. **Role-Based Access Control (RBAC)**
   - Three user roles: Admin, Analyst, Viewer
   - Granular permission management
   - Hierarchical access levels

4. **API Rate Limiting**
   - Protection against abuse and DOS attacks
   - Configurable limits per endpoint
   - User-specific rate limiting

5. **Audit Logging**
   - Comprehensive logging of all security events
   - Prediction request tracking
   - Failed authentication attempts
   - Data access monitoring

6. **Secure Environment Management**
   - Environment variable configuration
   - Secret key management
   - Configuration file security

---

## User Roles & Permissions

### 👑 Admin
- **Full System Access**
- Permissions:
  - View dashboard
  - Make single predictions
  - Make batch predictions
  - View all users
  - View audit logs
  - Manage users (future)
  - Export data

### 📊 Analyst
- **Data Analysis & Predictions**
- Permissions:
  - View dashboard
  - Make single predictions
  - Make batch predictions
  - Export data

### 👁️ Viewer
- **Read-Only Access**
- Permissions:
  - View dashboard
  - Make single predictions only

---

## Getting Started

### 1. Install Required Packages

```bash
pip install -r requirements.txt
```

New security packages added:
- `streamlit-authenticator>=0.2.3`
- `PyJWT>=2.8.0`
- `slowapi>=0.1.9`
- `python-jose[cryptography]>=3.3.0`
- `bcrypt>=4.0.1`
- `passlib[bcrypt]>=1.7.4`

### 2. Set Up Environment Variables

Copy the example environment file and customize:

```bash
cp .env.example .env
```

Edit `.env` and set your own secret keys:

```env
# Generate a secure secret key using:
# python -c "import secrets; print(secrets.token_hex(32))"

JWT_SECRET_KEY=your-super-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**⚠️ IMPORTANT:** Never commit `.env` to version control!

### 3. Configure Security Settings

Review and customize `config/security.yaml`:

```yaml
roles:
  admin:
    permissions:
      - read
      - write
      - predict
      - batch_predict
      - manage_users
```

---

## Default User Accounts

For demo purposes, the system includes three default accounts:

| Username | Password    | Role    | Description              |
|----------|-------------|---------|--------------------------|
| admin    | admin123    | Admin   | Full system access       |
| analyst  | analyst123  | Analyst | Analysis & predictions   |
| viewer   | viewer123   | Viewer  | Read-only access         |

**🔒 Production Note:** Change these credentials immediately in production!

---

## Using the Authenticated Dashboard

### Starting the Dashboard

```bash
streamlit run dashboard.py
```

### Login Process

1. Open dashboard in browser (usually http://localhost:8501)
2. You'll see the login page
3. Enter credentials:
   - Username: `admin`
   - Password: `admin123`
4. Click "Login"
5. Access the full dashboard upon successful authentication

### Features by Role

**Admin Users:**
- Full dashboard access
- View all metrics
- Export capabilities
- User management (upcoming)

**Analyst Users:**
- Dashboard access
- Make predictions
- View analytics

**Viewer Users:**
- Dashboard viewing
- Limited interaction
- No data export

---

## Using the Authenticated API

### 1. Obtain Access Token

#### Using cURL:

```bash
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

#### Using Python:

```python
import requests

# Login to get token
response = requests.post(
    "http://localhost:8000/token",
    data={
        "username": "admin",
        "password": "admin123"
    }
)

token_data = response.json()
access_token = token_data["access_token"]
print(f"Token: {access_token}")
```

#### Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "username": "admin",
  "role": "admin"
}
```

### 2. Make Authenticated Predictions

#### Single Prediction:

```python
import requests

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

customer_data = {
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
}

response = requests.post(
    "http://localhost:8000/predict",
    headers=headers,
    json=customer_data
)

prediction = response.json()
print(f"Churn Probability: {prediction['churn_probability']}")
print(f"Risk Level: {prediction['risk_level']}")
```

#### Batch Prediction (Analyst/Admin Only):

```python
batch_data = {
    "customers": [
        {
            "tenure_months": 24,
            "monthly_charges": 65.50,
            # ... other features
        },
        {
            "tenure_months": 12,
            "monthly_charges": 55.20,
            # ... other features
        }
    ],
    "threshold": 0.5
}

response = requests.post(
    "http://localhost:8000/predict_batch",
    headers=headers,
    json=batch_data
)

results = response.json()
print(f"Total Customers: {results['total_customers']}")
print(f"High Risk: {results['summary']['high_risk']}")
```

### 3. Check API Health (No Auth Required)

```bash
curl http://localhost:8000/health
```

---

## Rate Limiting

### Current Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/token` (Login) | 5 requests | 1 minute |
| `/predict` | 30 requests | 1 minute |
| `/predict_batch` | 10 requests | 1 minute |

### Rate Limit Response

When exceeded, you'll receive:

```json
{
  "error": "Rate limit exceeded",
  "detail": "30 per 1 minute"
}
```

**Status Code:** 429 (Too Many Requests)

---

## Audit Logging

### What's Logged

All security-relevant events are automatically logged:

1. **Authentication Events**
   - Successful logins
   - Failed login attempts
   - Logouts
   - Token creation

2. **Prediction Events**
   - Single predictions
   - Batch predictions
   - Failed predictions

3. **Access Events**
   - Dashboard views
   - Data exports
   - Admin actions

4. **Security Events**
   - Unauthorized access attempts
   - Rate limit violations
   - Invalid tokens

### Log Location

Audit logs are stored in: `./logs/audit/audit_YYYY-MM-DD.jsonl`

### Log Format

Each log entry is a JSON object:

```json
{
  "timestamp": "2025-12-28T12:30:45.123456",
  "event_type": "prediction_success",
  "username": "analyst",
  "user_role": "analyst",
  "ip_address": "192.168.1.100",
  "details": {
    "customer_id": "C12345",
    "churn_probability": 0.75,
    "risk_level": "HIGH"
  },
  "success": true,
  "error_message": null
}
```

### Viewing Audit Logs (Admin Only)

```python
# Get audit statistics
response = requests.get(
    "http://localhost:8000/admin/audit/stats?days=7",
    headers=headers
)

stats = response.json()
print(f"Total Events: {stats['total_events']}")
print(f"Failed Events: {stats['failed_events']}")
print(f"Unique Users: {stats['unique_users']}")
```

---

## Security Best Practices

### 🔒 Production Deployment

1. **Change Default Credentials**
   ```python
   # In auth/authentication.py, update or remove default users
   # Replace with database-backed user management
   ```

2. **Use Strong Secret Keys**
   ```bash
   # Generate secure keys
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

3. **Enable HTTPS**
   - Use SSL/TLS certificates
   - Set `COOKIE_SECURE=true` in `.env`
   - Update CORS settings

4. **Configure Firewall**
   - Restrict API access to known IPs
   - Use VPN for sensitive operations

5. **Regular Security Audits**
   - Review audit logs weekly
   - Monitor for suspicious activity
   - Update dependencies regularly

6. **Database Integration**
   - Replace in-memory user storage
   - Use encrypted password storage
   - Implement user session management

### 🛡️ Environment Security

```bash
# Restrict file permissions
chmod 600 .env
chmod 600 config/security.yaml

# Never commit secrets
echo ".env" >> .gitignore
echo "config/security.yaml" >> .gitignore  # if contains secrets
```

### 🔐 Password Management

```python
# Use strong password hashing (already implemented with bcrypt)
# Enforce password policies in production
# Implement password reset functionality
# Enable 2FA for admin accounts (future enhancement)
```

---

## API Documentation

### Interactive API Docs

Once the API is running, access:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Testing with Swagger

1. Go to http://localhost:8000/docs
2. Click "Authorize" button
3. Login via `/token` endpoint
4. Copy the access token
5. Enter: `Bearer <your_token>`
6. Try authenticated endpoints

---

## Troubleshooting

### Common Issues

#### 1. "Could not validate credentials"

**Cause:** Invalid or expired token

**Solution:**
- Request a new token via `/token`
- Check token expiration (default: 30 minutes)
- Verify token is included in Authorization header

#### 2. "Insufficient permissions"

**Cause:** User role lacks required permission

**Solution:**
- Check user role with `/admin/users` (admin only)
- Use appropriate account for the operation
- Contact admin to upgrade role

#### 3. "Rate limit exceeded"

**Cause:** Too many requests in time window

**Solution:**
- Wait for rate limit window to reset
- Optimize request patterns
- Use batch endpoints for multiple predictions

#### 4. Login fails with correct credentials

**Cause:** Database or authentication module issue

**Solution:**
- Check logs in `./logs/audit/`
- Verify authentication module is loaded
- Restart the application

#### 5. Dashboard shows login loop

**Cause:** Session state issue

**Solution:**
- Clear browser cache
- Check Streamlit session state
- Restart Streamlit application

---

## Advanced Topics

### Custom User Management

To replace in-memory users with database:

```python
# In auth/authentication.py

class AuthManager:
    def __init__(self, db_connection):
        self.db = db_connection
        # Remove _initialize_default_users()
    
    def get_user(self, username: str):
        # Query database instead of self.users_db
        return self.db.query_user(username)
```

### Implementing 2FA

```python
# Future enhancement
from pyotp import TOTP

def verify_2fa(user, token):
    totp = TOTP(user.secret_key)
    return totp.verify(token)
```

### Custom Permissions

```python
# Add custom permissions in security.yaml
roles:
  data_scientist:
    description: "ML Model Management"
    permissions:
      - read
      - predict
      - retrain_model
      - deploy_model
```

---

## Security Checklist

Before going to production:

- [ ] Change all default passwords
- [ ] Generate and set new JWT secret keys
- [ ] Enable HTTPS/SSL
- [ ] Configure proper CORS settings
- [ ] Set up database-backed user storage
- [ ] Enable audit log monitoring
- [ ] Configure rate limiting appropriately
- [ ] Restrict IP access if applicable
- [ ] Set up alerts for security events
- [ ] Test authentication thoroughly
- [ ] Document security procedures
- [ ] Train users on security practices

---

## Support & Contributing

### Getting Help

- Check audit logs for error details
- Review API documentation at `/docs`
- Consult application logs

### Reporting Security Issues

If you discover a security vulnerability:

1. **DO NOT** create a public GitHub issue
2. Email security concerns privately
3. Include detailed description
4. Wait for response before disclosure

---

## License & Compliance

This authentication system implements industry-standard security practices:

- JWT (RFC 7519)
- OAuth 2.0 compatible
- OWASP security guidelines
- GDPR consideration for audit logs

---

## Change Log

### Version 1.0 (December 2025)

- ✅ JWT token authentication
- ✅ Role-based access control
- ✅ API rate limiting
- ✅ Comprehensive audit logging
- ✅ Streamlit dashboard authentication
- ✅ Secure environment management

### Planned Features

- 🔜 Two-factor authentication (2FA)
- 🔜 Database-backed user management
- 🔜 Password reset functionality
- 🔜 Email notifications for security events
- 🔜 Advanced role customization
- 🔜 SSO/SAML integration

---

**Last Updated:** December 28, 2025  
**Version:** 1.0  
**Status:** Production Ready
