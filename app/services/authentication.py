
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional, Dict, Any
from pydantic import BaseModel
from app.models.user import User
from app.models.merchant import Merchant
from app.utils.encryption import verify_password
from app.utils.logging import log_activity
from config.database import get_db
from config.settings import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
    user_type: Optional[str] = None  # "user" or "merchant" or "admin"

class AuthenticationService:
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def authenticate_user(self, db: Session, username: str, password: str):
        user = db.query(User).filter(User.email == username).first()
        if not user:
            return False
        if not verify_password(password, user.password_hash):
            return False
        if not user.is_active:
            return False
        return user
    
    def authenticate_merchant(self, db: Session, username: str, password: str):
        merchant = db.query(Merchant).filter(Merchant.email == username).first()
        if not merchant:
            return False
        if not verify_password(password, merchant.password_hash):
            return False
        if not merchant.is_active:
            return False
        return merchant
    
    async def get_current_user(self, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
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
            if username is None or user_id is None or user_type is None:
                raise credentials_exception
            token_data = TokenData(username=username, user_id=user_id, user_type=user_type)
        except JWTError:
            raise credentials_exception
        
        if token_data.user_type == "user":
            user = db.query(User).filter(User.id == token_data.user_id).first()
            if user is None:
                raise credentials_exception
            return user
        elif token_data.user_type == "merchant":
            merchant = db.query(Merchant).filter(Merchant.id == token_data.user_id).first()
            if merchant is None:
                raise credentials_exception
            return merchant
        else:
            raise credentials_exception
    
    async def get_current_active_user(self, current_user: User = Depends(get_current_user)):
        if not current_user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
        return current_user
    
    async def login(self, db: Session, login_data: Dict[str, Any]):
        username = login_data.get("username")
        password = login_data.get("password")
        user_type = login_data.get("user_type", "user")  # Default to user
        
        if user_type == "user":
            user = self.authenticate_user(db, username, password)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = self.create_access_token(
                data={"sub": user.email, "user_id": user.id, "user_type": "user"},
                expires_delta=access_token_expires
            )
            log_activity("user_login", f"User {user.id} logged in")
            return {"access_token": access_token, "token_type": "bearer", "user_id": user.id, "user_type": "user"}
        
        elif user_type == "merchant":
            merchant = self.authenticate_merchant(db, username, password)
            if not merchant:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = self.create_access_token(
                data={"sub": merchant.email, "user_id": merchant.id, "user_type": "merchant"},
                expires_delta=access_token_expires
            )
            log_activity("merchant_login", f"Merchant {merchant.id} logged in")
            return {"access_token": access_token, "token_type": "bearer", "user_id": merchant.id, "user_type": "merchant"}
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user type",
            )

# Create an instance of the service
auth_service = AuthenticationService()

# Dependency to get the current active user
def get_current_active_user(current_user: User = Depends(auth_service.get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user