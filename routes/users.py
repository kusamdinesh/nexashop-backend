from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_pg_db
from models.user import User
from schemas.user import UserResponse, UserUpdate
from config.auth_utils import get_current_user, require_admin
import math

router = APIRouter()

@router.get("/", response_model=list[UserResponse])
def get_users(
    db: Session = Depends(get_pg_db),
    current_user: User = Depends(require_admin)
):
    """Admin only — get all users"""
    return db.query(User).all()

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Any logged in user — get own profile"""
    return current_user

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    data: UserUpdate,
    db: Session = Depends(get_pg_db),
    current_user: User = Depends(require_admin)
):
    """Admin only — update user role or status"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent admin from demoting themselves
    if str(user.id) == str(current_user.id) and data.role and data.role != "admin":
        raise HTTPException(
            status_code=400,
            detail="Cannot change your own role"
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    # Sync is_admin with role
    if data.role:
        user.is_admin = data.role == "admin"

    db.commit()
    db.refresh(user)
    return user

@router.delete("/{user_id}")
def delete_user(
    user_id: str,
    db: Session = Depends(get_pg_db),
    current_user: User = Depends(require_admin)
):
    """Admin only — deactivate a user"""
    if str(user_id) == str(current_user.id):
        raise HTTPException(
            status_code=400,
            detail="Cannot deactivate your own account"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    db.commit()
    return {"message": "User deactivated successfully"}