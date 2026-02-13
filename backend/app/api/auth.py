"""
Authentication API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.database import get_db
from app.schemas import UserLogin, Token, UserResponse
from app.dependencies import authenticate_user, create_access_token, get_current_user
from app.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


@router.post("/login", response_model=Token)
def login(user_login: UserLogin, db: Session = Depends(get_db)):
    """
    Login endpoint - authenticate user and return JWT token
    
    Args:
        user_login: Username and password
        db: Database session
        
    Returns:
        JWT access token
    """
    user = authenticate_user(db, user_login.username, user_login.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user.username})
    
    # Update last login
    user.last_login = datetime.now()
    db.commit()
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information
    
    Args:
        current_user: Current user from JWT token
        
    Returns:
        User information
    """
    return current_user


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """
    Logout endpoint (mainly for consistency - JWT tokens are stateless)
    
    Args:
        current_user: Current user
        
    Returns:
        Success message
    """
    return {"message": "Successfully logged out"}
