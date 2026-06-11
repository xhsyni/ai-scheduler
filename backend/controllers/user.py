from datetime import datetime, timedelta, timezone
from typing import Annotated
import bcrypt
import jwt
from fastapi.responses import JSONResponse
from fastapi import Depends, HTTPException, status, Request
from fastapi import Cookie
from services.db import DBService
from models.users import User
from fastapi.security import OAuth2PasswordBearer
import re 

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login", auto_error=False)

db = DBService()

SECRET_KEY = "ABCD@1234"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

def _hashed_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def _verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

def _create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Login Function
async def login(email,password):
    """
    This function is used to log in a user.
    """
    user = db.get_user_by_email(email)
    if not user or not _verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = _create_access_token(data={"sub": user.email})
    response = JSONResponse({"message": "Login successful","token_type": "bearer","access_token": access_token})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax"
    )
    return response

async def register(name: str, email: str, password: str):
    if not name or not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name, email, and password are required",
        )
    if re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format",
        )
    if db.get_user_by_email(email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )
    user = User(
        name=name,
        email=email,
        password=_hashed_password(password)
    )
    db.insert_user(user)
    return {"message": "User registered successfully"}
    
async def get_current_user(
    request: Request,
    access_token: str | None = Depends(oauth2_scheme)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1. Try Authorization header first
    token = access_token

    # 2. If no Authorization header, try HttpOnly cookie
    if not token:
        token = request.cookies.get("access_token")

    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")

        if email is None:
            raise credentials_exception

    except jwt.InvalidTokenError:
        raise credentials_exception

    user = db.get_user_by_email(email)

    if user is None:
        raise credentials_exception

    return user