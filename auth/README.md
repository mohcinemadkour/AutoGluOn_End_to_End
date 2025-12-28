# Authentication Module

This module provides comprehensive authentication and security features for the AutoGluon Churn Prediction system.

## Components

### `authentication.py`
- **AuthManager**: Main authentication manager class
- **User roles**: Admin, Analyst, Viewer
- **JWT token generation and validation**
- **Password hashing with bcrypt**
- **Role-based permission checking**
- **Streamlit authentication configuration**

### `audit_log.py`
- **AuditLogger**: Comprehensive event logging
- **Event tracking**: Login, predictions, data access, admin actions
- **Security event monitoring**: Unauthorized access, rate limits
- **JSON-line format logs** for easy parsing
- **Statistics and reporting**

## Quick Start

### Basic Usage

```python
from auth.authentication import AuthManager, UserRole
from auth.audit_log import get_audit_logger

# Initialize
auth_manager = AuthManager()
audit_logger = get_audit_logger()

# Authenticate user
user = auth_manager.authenticate_user("admin", "admin123")

if user:
    # Create JWT token
    from auth.authentication import create_access_token
    token = create_access_token(user.username, user.role, auth_manager)
    
    # Log the login
    audit_logger.log_login(user.username, success=True)
```

### FastAPI Integration

```python
from fastapi import Depends, Security
from fastapi.security import HTTPBearer
from auth.authentication import AuthManager, User

security = HTTPBearer()
auth_manager = AuthManager()

async def get_current_user(credentials = Security(security)) -> User:
    token = credentials.credentials
    token_data = auth_manager.decode_token(token)
    # ... validate and return user
```

### Streamlit Integration

```python
import streamlit as st
from auth.authentication import AuthManager

auth_manager = AuthManager()

# In your Streamlit app
username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Login"):
    user = auth_manager.authenticate_user(username, password)
    if user:
        st.session_state.authenticated = True
        st.session_state.user = user
```

## User Roles

### Admin
- Full system access
- User management
- Audit log viewing
- All prediction capabilities

### Analyst
- Data analysis
- Single & batch predictions
- Dashboard access
- Data export

### Viewer
- Read-only access
- Single predictions
- Dashboard viewing

## Default Users

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Admin |
| analyst | analyst123 | Analyst |
| viewer | viewer123 | Viewer |

**⚠️ Change these in production!**

## Audit Events

Tracked events include:
- `login_success` / `login_failed`
- `logout`
- `prediction_success` / `prediction_failed`
- `data_viewed` / `data_exported`
- `unauthorized_access`
- `rate_limit_exceeded`
- `user_created` / `user_modified`

## Configuration

### Environment Variables

```env
JWT_SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
AUDIT_LOG_DIR=./logs/audit
```

### Code Configuration

```python
# Custom secret key
auth_manager = AuthManager(
    secret_key="your-custom-secret",
    algorithm="HS256"
)

# Custom log directory
audit_logger = AuditLogger(log_dir="./custom/logs")
```

## Security Best Practices

1. **Use Strong Secret Keys**
   ```python
   import secrets
   secret_key = secrets.token_hex(32)
   ```

2. **Regular Password Updates**
   - Implement password expiration
   - Enforce strong password policies

3. **Monitor Audit Logs**
   ```python
   stats = audit_logger.get_statistics(days=7)
   failed = stats['failed_events']
   ```

4. **Replace In-Memory Storage**
   - Use database for production
   - Implement user session management

## API Reference

### AuthManager

```python
auth_manager = AuthManager(secret_key=None, algorithm="HS256")
auth_manager.create_user(username, email, password, role, full_name)
auth_manager.authenticate_user(username, password)
auth_manager.create_access_token(data, expires_delta)
auth_manager.decode_token(token)
auth_manager.check_permission(user_role, required_role)
```

### AuditLogger

```python
audit_logger = AuditLogger(log_dir=None)
audit_logger.log_login(username, success, ip_address)
audit_logger.log_prediction(username, user_role, prediction_data, success)
audit_logger.log_unauthorized_access(username, resource)
audit_logger.get_events(start_date, end_date, username, event_type)
audit_logger.get_statistics(days=7)
```

## Testing

```python
# Test authentication
def test_authentication():
    auth = AuthManager()
    
    # Valid login
    user = auth.authenticate_user("admin", "admin123")
    assert user is not None
    assert user.role == UserRole.ADMIN
    
    # Invalid login
    user = auth.authenticate_user("admin", "wrong")
    assert user is None

# Test authorization
def test_authorization():
    auth = AuthManager()
    
    # Admin can do everything
    assert auth.check_permission(UserRole.ADMIN, UserRole.VIEWER)
    assert auth.check_permission(UserRole.ADMIN, UserRole.ANALYST)
    
    # Viewer cannot do admin tasks
    assert not auth.check_permission(UserRole.VIEWER, UserRole.ADMIN)
```

## Troubleshooting

### Token Validation Fails
- Check token expiration
- Verify secret key matches
- Ensure token format is correct

### Audit Logs Not Created
- Check directory permissions
- Verify `AUDIT_LOG_DIR` is set
- Ensure sufficient disk space

### Authentication Loop
- Clear session state
- Check cookie expiration
- Verify user is not disabled

## Future Enhancements

- [ ] Database integration
- [ ] Two-factor authentication
- [ ] Password reset via email
- [ ] SSO/SAML support
- [ ] Advanced role customization
- [ ] IP whitelisting
- [ ] Session management UI

## License

Part of the AutoGluon Churn Prediction System
