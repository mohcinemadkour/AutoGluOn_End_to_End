"""
Audit Logging Module
Tracks all prediction requests, user actions, and security events
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
from enum import Enum
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    """Types of audit events"""
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    TOKEN_CREATED = "token_created"
    TOKEN_EXPIRED = "token_expired"
    
    # Prediction events
    PREDICTION_REQUEST = "prediction_request"
    PREDICTION_SUCCESS = "prediction_success"
    PREDICTION_FAILED = "prediction_failed"
    BATCH_PREDICTION = "batch_prediction"
    
    # Data access events
    DATA_VIEWED = "data_viewed"
    DATA_EXPORTED = "data_exported"
    DATA_MODIFIED = "data_modified"
    
    # Admin events
    USER_CREATED = "user_created"
    USER_MODIFIED = "user_modified"
    USER_DISABLED = "user_disabled"
    ROLE_CHANGED = "role_changed"
    
    # Security events
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_TOKEN = "invalid_token"


class AuditEvent:
    """Audit event model"""
    
    def __init__(
        self,
        event_type: AuditEventType,
        username: Optional[str] = None,
        user_role: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        self.timestamp = datetime.utcnow()
        self.event_type = event_type
        self.username = username or "anonymous"
        self.user_role = user_role
        self.ip_address = ip_address
        self.details = details or {}
        self.success = success
        self.error_message = error_message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "username": self.username,
            "user_role": self.user_role,
            "ip_address": self.ip_address,
            "details": self.details,
            "success": self.success,
            "error_message": self.error_message
        }
    
    def to_json(self) -> str:
        """Convert event to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


class AuditLogger:
    """
    Audit Logger for tracking all security-relevant events
    """
    
    def __init__(self, log_dir: Optional[str] = None):
        """
        Initialize AuditLogger
        
        Args:
            log_dir: Directory to store audit logs (default: ./logs/audit)
        """
        self.log_dir = Path(log_dir or os.getenv("AUDIT_LOG_DIR", "./logs/audit"))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Current log file
        self.log_file = self._get_log_file()
        
        logger.info(f"AuditLogger initialized. Log directory: {self.log_dir}")
    
    def _get_log_file(self) -> Path:
        """Get current log file path"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"audit_{date_str}.jsonl"
    
    def log_event(self, event: AuditEvent) -> None:
        """
        Log an audit event
        
        Args:
            event: AuditEvent to log
        """
        try:
            # Ensure we're using today's log file
            log_file = self._get_log_file()
            
            # Write event as JSON line
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(event.to_json() + '\n')
            
            # Also log to console for monitoring
            if not event.success:
                logger.warning(f"Audit: {event.event_type.value} - {event.username} - FAILED")
            else:
                logger.info(f"Audit: {event.event_type.value} - {event.username}")
        
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
    
    def log_login(self, username: str, success: bool, ip_address: Optional[str] = None,
                  error_message: Optional[str] = None) -> None:
        """Log login attempt"""
        event = AuditEvent(
            event_type=AuditEventType.LOGIN_SUCCESS if success else AuditEventType.LOGIN_FAILED,
            username=username,
            ip_address=ip_address,
            success=success,
            error_message=error_message
        )
        self.log_event(event)
    
    def log_logout(self, username: str, ip_address: Optional[str] = None) -> None:
        """Log logout"""
        event = AuditEvent(
            event_type=AuditEventType.LOGOUT,
            username=username,
            ip_address=ip_address
        )
        self.log_event(event)
    
    def log_prediction(self, username: str, user_role: str, 
                      prediction_data: Dict[str, Any],
                      success: bool = True,
                      error_message: Optional[str] = None,
                      ip_address: Optional[str] = None) -> None:
        """Log prediction request"""
        event = AuditEvent(
            event_type=AuditEventType.PREDICTION_SUCCESS if success else AuditEventType.PREDICTION_FAILED,
            username=username,
            user_role=user_role,
            ip_address=ip_address,
            details=prediction_data,
            success=success,
            error_message=error_message
        )
        self.log_event(event)
    
    def log_data_access(self, username: str, user_role: str, 
                       action: str, resource: str,
                       ip_address: Optional[str] = None) -> None:
        """Log data access"""
        event = AuditEvent(
            event_type=AuditEventType.DATA_VIEWED,
            username=username,
            user_role=user_role,
            ip_address=ip_address,
            details={"action": action, "resource": resource}
        )
        self.log_event(event)
    
    def log_unauthorized_access(self, username: str, resource: str,
                               ip_address: Optional[str] = None) -> None:
        """Log unauthorized access attempt"""
        event = AuditEvent(
            event_type=AuditEventType.UNAUTHORIZED_ACCESS,
            username=username,
            ip_address=ip_address,
            details={"resource": resource},
            success=False,
            error_message="Unauthorized access attempt"
        )
        self.log_event(event)
    
    def log_rate_limit(self, username: str, ip_address: Optional[str] = None) -> None:
        """Log rate limit exceeded"""
        event = AuditEvent(
            event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
            username=username,
            ip_address=ip_address,
            success=False,
            error_message="Rate limit exceeded"
        )
        self.log_event(event)
    
    def log_admin_action(self, admin_username: str, action: str,
                        target_username: Optional[str] = None,
                        details: Optional[Dict[str, Any]] = None) -> None:
        """Log administrative action"""
        event_details = details or {}
        if target_username:
            event_details["target_username"] = target_username
        event_details["action"] = action
        
        event = AuditEvent(
            event_type=AuditEventType.USER_MODIFIED,
            username=admin_username,
            user_role="admin",
            details=event_details
        )
        self.log_event(event)
    
    def get_events(self, 
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None,
                   username: Optional[str] = None,
                   event_type: Optional[AuditEventType] = None) -> List[Dict[str, Any]]:
        """
        Retrieve audit events with filters
        
        Args:
            start_date: Filter events after this date
            end_date: Filter events before this date
            username: Filter by username
            event_type: Filter by event type
        
        Returns:
            List of matching events
        """
        events = []
        
        try:
            # Determine which log files to read
            if start_date and end_date:
                # Read multiple files if date range spans multiple days
                current_date = start_date
                while current_date <= end_date:
                    date_str = current_date.strftime("%Y-%m-%d")
                    log_file = self.log_dir / f"audit_{date_str}.jsonl"
                    if log_file.exists():
                        events.extend(self._read_log_file(log_file))
                    current_date += timedelta(days=1)
            else:
                # Read today's log file
                log_file = self._get_log_file()
                if log_file.exists():
                    events = self._read_log_file(log_file)
            
            # Apply filters
            if username:
                events = [e for e in events if e.get("username") == username]
            
            if event_type:
                events = [e for e in events if e.get("event_type") == event_type.value]
            
            return events
        
        except Exception as e:
            logger.error(f"Failed to retrieve audit events: {e}")
            return []
    
    def _read_log_file(self, log_file: Path) -> List[Dict[str, Any]]:
        """Read events from a log file"""
        events = []
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        events.append(json.loads(line))
        except Exception as e:
            logger.error(f"Failed to read log file {log_file}: {e}")
        return events
    
    def get_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get audit statistics for the last N days
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary with statistics
        """
        from datetime import timedelta
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        events = self.get_events(start_date=start_date, end_date=end_date)
        
        stats = {
            "total_events": len(events),
            "period_days": days,
            "events_by_type": {},
            "events_by_user": {},
            "failed_events": 0,
            "unique_users": set(),
            "unique_ips": set()
        }
        
        for event in events:
            # Count by type
            event_type = event.get("event_type")
            stats["events_by_type"][event_type] = stats["events_by_type"].get(event_type, 0) + 1
            
            # Count by user
            username = event.get("username")
            stats["events_by_user"][username] = stats["events_by_user"].get(username, 0) + 1
            stats["unique_users"].add(username)
            
            # Track IPs
            if event.get("ip_address"):
                stats["unique_ips"].add(event["ip_address"])
            
            # Count failures
            if not event.get("success", True):
                stats["failed_events"] += 1
        
        # Convert sets to counts
        stats["unique_users"] = len(stats["unique_users"])
        stats["unique_ips"] = len(stats["unique_ips"])
        
        return stats


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
