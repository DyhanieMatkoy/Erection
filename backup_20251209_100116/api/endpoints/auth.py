"""
Authentication endpoints
"""
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from api.models.auth import LoginRequest, LoginResponse, UserInfo
from api.services.auth_service import AuthService
from api.dependencies.auth import get_current_user, get_auth_service
from api.dependencies.database import get_db
from api.config import settings


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login endpoint
    
    Authenticates user and returns JWT token
    
    Args:
        request: Login credentials
        db: Database session
        
    Returns:
        LoginResponse with JWT token and user info
        
    Raises:
        HTTPException: If authentication fails
    """
    # Create auth service with database session
    auth_service = AuthService(db=db)
    
    # Authenticate user
    user = auth_service.authenticate_user(request.username, request.password, db=db)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = auth_service.create_access_token(
        user_id=user["id"],
        username=user["username"],
        role=user["role"]
    )
    
    # Calculate expires_in (in seconds)
    expires_in = settings.JWT_EXPIRATION_HOURS * 3600
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserInfo(**user)
    )


@router.get("/me", response_model=UserInfo)
async def get_me(current_user: UserInfo = Depends(get_current_user)):
    """
    Get current user information
    
    Requires valid JWT token in Authorization header
    """
    return current_user
