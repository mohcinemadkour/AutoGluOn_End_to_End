"""
Authentication and Security Module
"""

from .authentication import (
    AuthManager, 
    UserRole, 
    User,
    UserInDB,
    Token,
    TokenData,
    authenticate_user,
    create_access_token
)
from .audit_log import (
    AuditLogger, 
    AuditEvent,
    AuditEventType,
    get_audit_logger
)

__all__ = [
    'AuthManager',
    'UserRole',
    'User',
    'UserInDB',
    'Token',
    'TokenData',
    'authenticate_user',
    'create_access_token',
    'AuditLogger',
    'AuditEvent',
    'AuditEventType',
    'get_audit_logger'
]
