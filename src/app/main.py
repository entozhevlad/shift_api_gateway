from fastapi import FastAPI, HTTPException, Depends, Query
from typing import Optional
from fastapi.security import OAuth2PasswordRequestForm
import httpx
from pydantic import BaseModel, Field
from datetime import datetime

app = FastAPI()

# URLs микросервисов
AUTH_SERVICE_URL = "http://auth_service:82"
TRANSACTION_SERVICE_URL = "http://transactions_service:83"

class TransactionCreateRequest(BaseModel):
    amount: float  # сумма должна быть положительной
    type: str = Field(..., pattern=r"^(debit|credit)$")  # допустимые типы транзакций

class DateRangeRequest(BaseModel):
    start: datetime = Field(..., description="Начало временного диапазона")
    end: datetime = Field(..., description="Конец временного диапазона")

# Регистрация пользователя
@app.post("/register")
async def register(
    username: str = Query(...),
    password: str = Query(...),
    first_name: Optional[str] = Query(None),
    last_name: Optional[str] = Query(None)
):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AUTH_SERVICE_URL}/register",
            params={
                "username": username,
                "password": password,
                "first_name": first_name,
                "last_name": last_name
            }
        )
        if response.status_code == 200:
            return response.json()
        raise HTTPException(status_code=response.status_code, detail=response.json().get("detail"))

# Логин пользователя
@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    async with httpx.AsyncClient() as client:
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "username": form_data.username,
            "password": form_data.password,
        }
        response = await client.post(f"{AUTH_SERVICE_URL}/login", data=data, headers=headers)
        if response.status_code == 200:
            return response.json()
        raise HTTPException(status_code=response.status_code, detail=response.json().get("detail"))

# Создание транзакции
@app.post("/transactions/")
async def create_transaction(request: TransactionCreateRequest, token: str = Query(...)):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TRANSACTION_SERVICE_URL}/transaction/transactions/",
            json={
                "amount": request.amount,
                "type": request.type
            },
            params={"token": token}  # Передача токена в микросервис
        )
        if response.status_code == 200:
            return response.json()
        raise HTTPException(status_code=response.status_code, detail=response.json().get("detail"))

# Получение отчета по транзакциям
@app.post("/transactions/report/")
async def get_transactions_report(request: DateRangeRequest, token: str = Query(...)):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TRANSACTION_SERVICE_URL}/transaction/transactions/report/",
            json={
                "start": request.start.isoformat(),
                "end": request.end.isoformat()
            },
            params={"token": token}  # Передача токена в микросервис
        )
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
            response = await client.get(f"{TRANSACTION_SERVICE_URL}/transaction/healthz/ready")
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
