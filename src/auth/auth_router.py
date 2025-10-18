from fastapi import APIRouter, Depends
from pydantic import BaseModel
from dependencies import get_auth_service

router = APIRouter(prefix="/auth")

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
async def login(
    request: LoginRequest,
    auth_service = Depends(get_auth_service)
):
    # AuthService를 통한 로그인 처리
    access_token = auth_service.login(request.username, request.password)
    return {"access_token": access_token}