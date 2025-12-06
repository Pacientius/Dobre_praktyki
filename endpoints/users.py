from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import get_password_hash, get_current_user, require_role
from database.database import get_db
from database.model import User, UserCreate, UserUpdate, UserResponse

router = APIRouter()


@router.get("/{user_id}", response_model=UserResponse, dependencies=[Depends(get_current_user)])
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/", response_model=UserResponse, dependencies=[Depends(require_role("ADMIN"))])
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = get_password_hash(user.password)
    new_user = User(name=user.name, password=hashed_password, roles=user.roles)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.put("/{user_id}", response_model=UserResponse, dependencies=[Depends(get_current_user)])
async def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user_update.model_dump(exclude_unset=True)

    if "password" in update_data:
        update_data["password"] = get_password_hash(update_data["password"])

    for field, value in update_data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user

@router.delete("/{user_id}", dependencies=[Depends(require_role("ADMIN"))])
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}