from fastapi import FastAPI
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from auth import create_access_token, get_user, verify_password, get_current_user, get_password_hash

from endpoints import users
from database.database import get_db, engine, Base
from database.model import User
from database.user_add_admin import create_admin_user


app = FastAPI()


Base.metadata.create_all(bind=engine)

create_admin_user()

@app.get("/")
async def hello():
    return {"message": "Hello World"}

#logowanie zeby muc uzyc ruterow
@app.post("/login")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user(db, form_data.username)
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.name, "roles": user.roles}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/user_details")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return {"username": current_user.name, "roles": current_user.roles}


app.include_router(
    users.router,
    prefix="/users",
    tags=["users"],
)


