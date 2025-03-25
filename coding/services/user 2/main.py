from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
import os

from . import models, schemas
from .database import get_db, init_db, run_migrations

# Initialize password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI(title="User Service")

# Initialize database and run migrations
init_db()
run_migrations()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    cursor = Depends(get_db)
) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user = models.User.get_by_id(cursor, payload["sub"])
        if user is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

@app.post("/register", response_model=schemas.User)
async def register(
    user: schemas.UserCreate,
    cursor = Depends(get_db)
):
    # Check if username exists
    if models.User.get_by_username(cursor, user.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email exists
    if models.User.get_by_email(cursor, user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    hashed_password = get_password_hash(user.password)
    db_user = models.User.create(cursor, user.username, user.email, hashed_password)
    
    return db_user

@app.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    cursor = Depends(get_db)
):
    user = models.User.get_by_username(cursor, form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = create_access_token({"sub": user["id"]})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@app.get("/users/me", response_model=schemas.User)
async def read_users_me(
    current_user: dict = Depends(get_current_user)
):
    return current_user

@app.get("/users/{user_id}", response_model=schemas.User)
async def get_user(
    user_id: int,
    cursor = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user = models.User.get_by_id(cursor, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/users/", response_model=List[schemas.User])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    cursor = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    users = models.User.list_users(cursor, skip, limit)
    return users

@app.post("/users/{user_id}/roles/{role_name}")
async def add_user_role(
    user_id: int,
    role_name: str,
    cursor = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Check if user has admin role
    if "admin" not in current_user["roles"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    if not models.Role.add_user_role(cursor, user_id, role_name):
        raise HTTPException(status_code=400, detail="Invalid role or user")
    
    return {"message": "Role added successfully"}

@app.delete("/users/{user_id}/roles/{role_name}")
async def remove_user_role(
    user_id: int,
    role_name: str,
    cursor = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Check if user has admin role
    if "admin" not in current_user["roles"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    if not models.Role.remove_user_role(cursor, user_id, role_name):
        raise HTTPException(status_code=400, detail="Invalid role or user")
    
    return {"message": "Role removed successfully"}