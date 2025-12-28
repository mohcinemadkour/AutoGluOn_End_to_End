"""
Authentication and Authorization Module
Provides JWT token-based authentication and role-based access control
"""

import os
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum
import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRole(str, Enum):
    """User roles for role-based access control"""
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class User(BaseModel):
    """User model"""
    username: str
    email: str
    role: UserRole
    full_name: Optional[str] = None
    disabled: bool = False


class UserInDB(User):
    """User model with hashed password"""
    hashed_password: str


class Token(BaseModel):
    """JWT token model"""
    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    """Token payload data"""
    username: Optional[str] = None
    role: Optional[str] = None


class AuthManager:
    """
    Authentication Manager for handling user authentication and authorization
    """
    
    def __init__(self, secret_key: Optional[str] = None, algorithm: str = "HS256"):
        """
        Initialize AuthManager
        
        Args:
            secret_key: Secret key for JWT encoding/decoding
            algorithm: JWT algorithm (default: HS256)
        """
        self.secret_key = secret_key or os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithm = algorithm
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        
        # In-memory user database (replace with real database in production)
        self.users_db: Dict[str, UserInDB] = {}
        self._initialize_default_users()
    
    def _initialize_default_users(self):
        """Initialize default users (for demo purposes)"""
        default_users = [
            {
                "username": "admin",
                "email": "admin@example.com",
                "password": "admin123",
                "role": UserRole.ADMIN,
                "full_name": "Admin User"
            },
            {
                "username": "analyst",
                "email": "analyst@example.com",
                "password": "analyst123",
                "role": UserRole.ANALYST,
                "full_name": "Data Analyst"
            },
            {
                "username": "viewer",
                "email": "viewer@example.com",
                "password": "viewer123",
                "role": UserRole.VIEWER,
                "full_name": "Viewer User"
            }
        ]
        
        for user_data in default_users:
            password = user_data.pop("password")
            self.create_user(password=password, **user_data)
    
    def _prepare_password(self, password: str) -> str:
        """
        Prepare password for bcrypt by pre-hashing if necessary.
        Bcrypt has a 72-byte limit, so we hash long passwords with SHA256 first.
        """
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            # Pre-hash with SHA256 for long passwords
            return hashlib.sha256(password_bytes).hexdigest()
        return password
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        prepared_password = self._prepare_password(plain_password)
        return pwd_context.verify(prepared_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        prepared_password = self._prepare_password(password)
        return pwd_context.hash(prepared_password)
    
    def get_user(self, username: str) -> Optional[UserInDB]:
        """Get user from database"""
        return self.users_db.get(username)
    
    def create_user(self, username: str, email: str, password: str, 
                   role: UserRole, full_name: Optional[str] = None) -> UserInDB:
        """Create a new user"""
        if username in self.users_db:
            raise ValueError(f"User {username} already exists")
        
        user = UserInDB(
            username=username,
            email=email,
            role=role,
            full_name=full_name,
            hashed_password=self.get_password_hash(password)
        )
        self.users_db[username] = user
        return user
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username and password"""
        user = self.get_user(username)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        if user.disabled:
            return None
        return User(**user.dict())
    
    def create_access_token(self, data: Dict[str, Any], 
                          expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def decode_token(self, token: str) -> Optional[TokenData]:
        """Decode and validate a JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            role: str = payload.get("role")
            
            if username is None:
                return None
            
            return TokenData(username=username, role=role)
        except InvalidTokenError:
            return None
    
    def check_permission(self, user_role: UserRole, required_role: UserRole) -> bool:
        """
        Check if user has required permission
        
        Permission hierarchy: ADMIN > ANALYST > VIEWER
        """
        role_hierarchy = {
            UserRole.ADMIN: 3,
            UserRole.ANALYST: 2,
            UserRole.VIEWER: 1
        }
        
        return role_hierarchy[user_role] >= role_hierarchy[required_role]
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users (excluding passwords)"""
        return [
            {
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "full_name": user.full_name,
                "disabled": user.disabled
            }
            for user in self.users_db.values()
        ]
    
    def update_user_role(self, username: str, new_role: UserRole) -> bool:
        """Update user role"""
        user = self.get_user(username)
        if not user:
            return False
        user.role = new_role
        return True
    
    def disable_user(self, username: str) -> bool:
        """Disable a user account"""
        user = self.get_user(username)
        if not user:
            return False
        user.disabled = True
        return True
    
    def enable_user(self, username: str) -> bool:
        """Enable a user account"""
        user = self.get_user(username)
        if not user:
            return False
        user.disabled = False
        return True


# Convenience functions
def authenticate_user(username: str, password: str, auth_manager: AuthManager) -> Optional[User]:
    """Authenticate a user"""
    return auth_manager.authenticate_user(username, password)


def create_access_token(username: str, role: UserRole, auth_manager: AuthManager) -> Token:
    """Create an access token for a user"""
    access_token_expires = timedelta(minutes=auth_manager.access_token_expire_minutes)
    access_token = auth_manager.create_access_token(
        data={"sub": username, "role": role},
        expires_delta=access_token_expires
    )
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=auth_manager.access_token_expire_minutes * 60
    )


# Streamlit-specific authentication helpers
class StreamlitAuthConfig:
    """Configuration for Streamlit Authenticator"""
    
    @staticmethod
    def get_config(auth_manager: AuthManager) -> Dict[str, Any]:
        """Generate config for streamlit-authenticator"""
        credentials = {
            "usernames": {}
        }
        
        for username, user in auth_manager.users_db.items():
            credentials["usernames"][username] = {
                "email": user.email,
                "name": user.full_name or username,
                "password": user.hashed_password,
                "role": user.role.value
            }
        
        config = {
            "credentials": credentials,
            "cookie": {
                "name": "autogluon_auth_cookie",
                "key": auth_manager.secret_key,
                "expiry_days": 30
            },
            "preauthorized": {
                "emails": []
            }
        }
        
        return config
