import httpx
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, Field, condecimal
from fastapi.security import OAuth2PasswordRequestForm
from src.app.external.auth_service.src.app.services.auth_service import AuthService, oauth2_scheme
from datetime import datetime
from typing import Optional

app = FastAPI()

# URLs микросервисов
AUTH_SERVICE_URL = "http://auth_service:82"
TRANSACTION_SERVICE_URL = "http://transactions_service:83"

# Сервис аутентификации
auth_service = AuthService()

# Модели запросов
class UserCredentials(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)

class TransactionCreateRequest(BaseModel):
    amount: condecimal(gt=0)  # сумма должна быть положительной
    type: str = Field(..., pattern=r"^(deposit|withdrawal)$")  # допустимые типы транзакций

class DateRangeRequest(BaseModel):
    start: datetime = Field(..., description="Начало временного диапазона")
    end: datetime = Field(..., description="Конец временного диапазона")

# Получение текущего пользователя
async def get_current_user(token: str = Depends(oauth2_scheme)):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{AUTH_SERVICE_URL}/verify", headers={"Authorization": f"Bearer {token}"})
            response.raise_for_status()
            return response.json()["user"]
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.json().get("detail", "Invalid token"))

# Регистрация пользователя
@app.post("/register")
async def register(user_credentials: UserCredentials):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{AUTH_SERVICE_URL}/register", json=user_credentials.dict())
        if response.status_code == 200:
            return response.json()
        raise HTTPException(status_code=response.status_code, detail=response.json().get("detail"))

# Логин пользователя
@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    async with httpx.AsyncClient() as client:
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "password",
            "username": form_data.username,
            "password": form_data.password,
        }
        response = await client.post(f"{AUTH_SERVICE_URL}/login", data=data, headers=headers)
        if response.status_code == 200:
            return response.json()
        raise HTTPException(status_code=response.status_code, detail=response.json().get("detail"))

# Создание транзакции
@app.post("/transactions/create_transaction/")
async def create_transaction(request: TransactionCreateRequest, current_user: str = Depends(get_current_user)):
    request_data = {
        "user_id": current_user,  # добавляем идентификатор пользователя
        "amount": request.amount,
        "type": request.type
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{TRANSACTION_SERVICE_URL}/transactions/", json=request_data)
        if response.status_code == 200:
            return response.json()
        raise HTTPException(status_code=response.status_code, detail=response.json().get("detail"))

# Получение отчета по транзакциям
@app.post("/transactions/report/")
async def get_transactions_report(request: DateRangeRequest, current_user: str = Depends(get_current_user)):
    request_data = {
        "user_id": current_user,
        "start": request.start.isoformat(),
        "end": request.end.isoformat()
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{TRANSACTION_SERVICE_URL}/transactions/report/", json=request_data)
        if response.status_code == 200:
            return response.json()
        raise HTTPException(status_code=response.status_code, detail=response.json().get("detail"))

# Проверка здоровья аутентификационного сервиса
async def check_auth_service_health():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{AUTH_SERVICE_URL}/healthz/ready")
            response.raise_for_status()
            return response.status_code == 200
        except httpx.RequestError:
            return False

# Проверка здоровья сервиса транзакций
async def check_transaction_service_health():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{TRANSACTION_SERVICE_URL}/healthz/ready")
            response.raise_for_status()
            return response.status_code == 200
        except httpx.RequestError:
            return False

# Проверка состояния всех сервисов
@app.get("/healthz/ready")
async def health_check():
    auth_healthy = await check_auth_service_health()
    transaction_healthy = await check_transaction_service_health()

    if not auth_healthy or not transaction_healthy:
        raise HTTPException(status_code=503, detail="One or more dependencies are not available")

    return {"status": "healthy"}
