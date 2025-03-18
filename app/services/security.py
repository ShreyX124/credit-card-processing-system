from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from typing import Optional, List, Dict, Any
from app.models.user import User
from app.utils.logging import log_activity
from config.database import get_db
from config.settings import SECRET_KEY, ALGORITHM
from app.services.authentication import auth_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class SecurityService:
    def __init__(self):
        self.rate_limit_cache = {}
        self.ip_blacklist = set()
        self.security_policies = {
            "password_min_length": 8,
            "password_requires_uppercase": True,
            "password_requires_special_char": True,
            "password_requires_number": True,
            "max_login_attempts": 5,
            "lockout_duration_minutes": 15,
            "session_timeout_minutes": 30,
        }
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """
        Validate password strength based on security policies
        """
        has_uppercase = any(char.isupper() for char in password)
        has_special_char = any(not char.isalnum() for char in password)
        has_number = any(char.isdigit() for char in password)
        has_min_length = len(password) >= self.security_policies["password_min_length"]
        
        is_valid = (
            has_min_length and
            (not self.security_policies["password_requires_uppercase"] or has_uppercase) and
            (not self.security_policies["password_requires_special_char"] or has_special_char) and
            (not self.security_policies["password_requires_number"] or has_number)
        )
        
        return {
            "is_valid": is_valid,
            "requirements": {
                "min_length": self.security_policies["password_min_length"],
                "requires_uppercase": self.security_policies["password_requires_uppercase"],
                "requires_special_char": self.security_policies["password_requires_special_char"],
                "requires_number": self.security_policies["password_requires_number"],
            },
            "validation": {
                "has_min_length": has_min_length,
                "has_uppercase": has_uppercase,
                "has_special_char": has_special_char,
                "has_number": has_number,
            }
        }
    
    def check_rate_limit(self, ip_address: str, action: str, limit: int = 100, window_seconds: int = 3600) -> bool:
        """
        Check if the IP address has exceeded the rate limit for a specific action
        """
        import time
        current_time = time.time()
        cache_key = f"{ip_address}:{action}"
        
        if cache_key not in self.rate_limit_cache:
            self.rate_limit_cache[cache_key] = []
        
        # Remove old requests outside the window
        self.rate_limit_cache[cache_key] = [
            timestamp for timestamp in self.rate_limit_cache[cache_key]
            if current_time - timestamp <= window_seconds
        ]
        
        # Check if limit is exceeded
        if len(self.rate_limit_cache[cache_key]) >= limit:
            log_activity(
                "rate_limit_exceeded",
                f"Rate limit exceeded for IP {ip_address} on action {action}"
            )
            return False
        
        # Add current request
        self.rate_limit_cache[cache_key].append(current_time)
        return True
    
    def is_ip_blacklisted(self, ip_address: str) -> bool:
        """
        Check if the IP address is blacklisted
        """
        return ip_address in self.ip_blacklist
    
    def blacklist_ip(self, ip_address: str):
        """
        Add an IP address to the blacklist
        """
        self.ip_blacklist.add(ip_address)
        log_activity("ip_blacklisted", f"IP address {ip_address} blacklisted")
    
    def remove_ip_from_blacklist(self, ip_address: str):
        """
        Remove an IP address from the blacklist
        """
        if ip_address in self.ip_blacklist:
            self.ip_blacklist.remove(ip_address)
            log_activity("ip_unblacklisted", f"IP address {ip_address} removed from blacklist")
    
    def get_security_policies(self) -> Dict[str, Any]:
        """
        Get the current security policies
        """
        return self.security_policies
    
    def update_security_policies(self, new_policies: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update security policies
        """
        self.security_policies.update(new_policies)
        log_activity("security_policies_updated", "Security policies updated")
        return self.security_policies
    
    def sanitize_input(self, input_data: str) -> str:
        """
        Sanitize input data to prevent XSS attacks
        """
        import html
        return html.escape(input_data)
    
    def detect_sql_injection(self, input_data: str) -> bool:
        """
        Detect potential SQL injection attempts
        """
        sql_patterns = [
            "SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "UNION", "ALTER",
            "EXEC", "EXECUTE", "DECLARE", "CREATE", "--", "1=1", "OR 1=1"
        ]
        
        input_upper = input_data.upper()
        for pattern in sql_patterns:
            if pattern in input_upper:
                log_activity("sql_injection_attempt", f"Potential SQL injection: {input_data}")
                return True
        
        return False

# Create an instance of the service
security_service = SecurityService()

# Dependency to check admin permissions
async def check_admin_permissions(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        user_type: str = payload.get("user_type")
        if username is None or user_id is None:
            raise credentials_exception
            
        if user_type != "user":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
            
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
            
    except JWTError:
        raise credentials_exception
    
    return True