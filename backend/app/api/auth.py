from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db, SessionLocal
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse, UserCreateRequest
from app.utils.security import hash_password, verify_password, create_access_token
from app.utils.auth_deps import get_current_user, require_admin
from app.utils.logger import logger

router = APIRouter(prefix="/auth", tags=["auth"])


def seed_default_admin():
    """Ensure a default admin user exists if the user database is empty."""
    db: Session = SessionLocal()
    try:
        user_count = db.query(User).count()
        if user_count == 0:
            logger.info("No existing users found. Seeding initial administrator account...")
            admin_user = User(
                username="admin",
                email="admin@netsecurelab.local",
                hashed_password=hash_password("NetSecureLab#2026!"),
                role="admin",
                is_active=True,
            )
            db.add(admin_user)
            db.commit()
            logger.info("Default administrator created (username: 'admin').")
    except Exception as e:
        logger.error(f"Error seeding default admin user: {e}")
    finally:
        db.close()


@router.post("/login", response_model=TokenResponse)
def login(creds: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user credentials and return signed JWT bearer token."""
    user = db.query(User).filter(User.username == creds.username).first()
    if not user or not verify_password(creds.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    token = create_access_token({"sub": user.username, "role": user.role, "id": user.id})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get profile information for the currently authenticated user."""
    return current_user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    user_in: UserCreateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """Register a new user account (requires admin privilege)."""
    existing = db.query(User).filter(User.username == user_in.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{user_in.username}' is already registered",
        )

    new_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        role=user_in.role or "operator",
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
