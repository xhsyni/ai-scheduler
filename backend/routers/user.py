from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta, timezone
from typing import Annotated
from controllers.user import login as controller_login, register as controller_register, get_current_user
from fastapi import APIRouter
from pydantic import BaseModel

class RegisterModel(BaseModel):
    name: str
    email: str
    password: str

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.post("/login")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    email = form_data.username
    password = form_data.password
    response = await controller_login(email,password)

    return response


@router.post("/register")
async def register(body: RegisterModel):
    response = await controller_register(body.name, body.email, body.password)
    return response


@router.get("/me")
async def read_users_me(current_user: Annotated[dict, Depends(get_current_user)]):
    """
    A protected route. 
    Requires a valid JWT token in the 'Authorization: Bearer <token>' header.
    """
    return {"user": current_user}
