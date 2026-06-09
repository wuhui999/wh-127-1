from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from database import get_db
from models import User
from schemas import LoginRequest, LoginResponse, UserCreate, UserResponse
from auth import (
    verify_password,
    hash_password,
    create_access_token,
    get_current_user,
    require_role,
)

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == request.username).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    token = create_access_token(
        data={"user_id": user.id, "username": user.username, "role": user.role}
    )
    return LoginResponse(token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.get("/users", response_model=list[UserResponse])
def list_users(
    role: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    return query.all()


@router.post("/register", response_model=UserResponse)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )
    valid_roles = {"beekeeper", "orchard_owner", "supervisor", "admin"}
    if user_data.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的角色，有效角色: {', '.join(valid_roles)}",
        )
    user = User(
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        real_name=user_data.real_name,
        role=user_data.role,
        phone=user_data.phone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)
