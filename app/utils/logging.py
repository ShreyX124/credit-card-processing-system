import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

# Create logger
logger = logging.getLogger("credit_card_processing")

class ActivityLog:
    def __init__(self):
        self.log_directory = "logs"
        # Create the log directory if it doesn't exist
        os.makedirs(self.log_directory, exist_ok=True)
        self.activity_log_file = os.path.join(self.log_directory, "activity.log")
        self.security_log_file = os.path.join(self.log_directory, "security.log")
        self.error_log_file = os.path.join(self.log_directory, "error.log")
    
    def log_to_file(self, log_file: str, log_data: Dict[str, Any]):
        """
        Log data to a specific log file
        """
        with open(log_file, "a") as f:
            f.write(json.dumps(log_data) + "\n")
    
    def log_activity(self, action: str, description: str, user_id: Optional[int] = None, 
                     ip_address: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """
        Log user activity
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "description": description,
            "user_id": user_id,
            "ip_address": ip_address
        }
        
        if metadata:
            log_data["metadata"] = metadata
        
        # Log to application log
        logger.info(f"Activity: {description}")
        
        # Log to activity log file
        self.log_to_file(self.activity_log_file, log_data)
        
        # Log security-related events to security log file
        security_actions = ["login", "logout", "password_change", "failed_login", 
                           "fraud_detection", "blacklist", "permission_change"]
        if any(security_action in action for security_action in security_actions):
            self.log_to_file(self.security_log_file, log_data)
    
    def log_error(self, error_type: str, error_message: str, user_id: Optional[int] = None,
                 ip_address: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """
        Log errors
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": error_type,
            "error_message": error_message,
            "user_id": user_id,
            "ip_address": ip_address
        }
        
        if metadata:
            log_data["metadata"] = metadata
        
        # Log to application log
        logger.error(f"Error: {error_message}")
        
        # Log to error log file
        self.log_to_file(self.error_log_file, log_data)
    
    def get_recent_activities(self, limit: int = 100) -> list:
        """
        Get recent activities from the log file
        """
        activities = []
        try:
            with open(self.activity_log_file, "r") as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    activities.append(json.loads(line))
        except (FileNotFoundError, json.JSONDecodeError):
            # Return empty list if file doesn't exist or has invalid JSON
            pass
        return activities
    
    def get_recent_errors(self, limit: int = 100) -> list:
        """
        Get recent errors from the log file
        """
        errors = []
        try:
            with open(self.error_log_file, "r") as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    errors.append(json.loads(line))
        except (FileNotFoundError, json.JSONDecodeError):
            # Return empty list if file doesn't exist or has invalid JSON
            pass
        return errors
    
    def get_security_logs(self, limit: int = 100) -> list:
        """
        Get security logs from the log file
        """
        security_logs = []
        try:
            with open(self.security_log_file, "r") as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    security_logs.append(json.loads(line))
        except (FileNotFoundError, json.JSONDecodeError):
            # Return empty list if file doesn't exist or has invalid JSON
            pass
        return security_logs

# Create an instance of ActivityLog
activity_logger = ActivityLog()

# Function to log activity, for simpler imports
def log_activity(action: str, description: str, user_id: Optional[int] = None, 
                ip_address: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
    activity_logger.log_activity(action, description, user_id, ip_address, metadata)

# Function to log errors, for simpler imports
def log_error(error_type: str, error_message: str, user_id: Optional[int] = None,
             ip_address: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
    activity_logger.log_error(error_type, error_message, user_id, ip_address, metadata)