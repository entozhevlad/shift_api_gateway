import httpx
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from src.app.external.auth_service.src.app.services.auth_service import AuthService, oauth2_scheme
from fastapi.security import OAuth2PasswordRequestForm  # <-- Добавьте этот импорт


app = FastAPI()

AUTH_SERVICE_URL = "http://auth_service:82"
TRANSACTION_SERVICE_URL = "http://transactions_service:83"

auth_service = AuthService()

class UserCredentials(BaseModel):
    username: str
    password: str


class TransactionCreateRequest(BaseModel):
    user_id: str
    amount: float
    type: str


class DateRangeRequest(BaseModel):
    start: str
    end: str
    user_id: str


async def get_current_user(token: str = Depends(oauth2_scheme)):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{AUTH_SERVICE_URL}/verify", headers={"Authorization": f"Bearer {token}"})
            response.raise_for_status()
            return response.json()["user"]
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.json().get("detail", "Invalid token"))


@app.post("/register")
async def register(user_credentials: UserCredentials):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{AUTH_SERVICE_URL}/register", json=user_credentials.dict())
        if response.status_code == 200:
            return response.json()
        raise HTTPException(status_code=response.status_code,
                            detail=response.json().get("detail"))


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
        raise HTTPException(status_code=response.status_code,
                            detail=response.json().get("detail"))

@app.post("/transactions/create_transaction/")
async def create_transaction(request: TransactionCreateRequest, current_user: str = Depends(get_current_user)):
    request.user_id = current_user

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{TRANSACTION_SERVICE_URL}/transactions/", json=request.dict())
        if response.status_code == 200:
            return response.json()
        raise HTTPException(status_code=response.status_code,
                            detail=response.json().get("detail"))


@app.post("/transactions/report/")
async def get_transactions_report(request: DateRangeRequest, current_user: str = Depends(get_current_user)):
    request.user_id = current_user

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{TRANSACTION_SERVICE_URL}/transactions/report/", json=request.dict())
        if response.status_code == 200:
            return response.json()
        raise HTTPException(status_code=response.status_code,
                            detail=response.json().get("detail"))


async def check_auth_service_health():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{AUTH_SERVICE_URL}/healthz/ready")
            response.raise_for_status()  # Если статус не 200, возникнет исключение
            return response.status_code == 200
        except httpx.RequestError:
            return False

async def check_transaction_service_health():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{TRANSACTION_SERVICE_URL}/transaction/healthz/ready")
            response.raise_for_status()  # Если статус не 200, возникнет исключение
            return response.status_code == 200
        except httpx.RequestError:
            return False

@app.get("/healthz/ready")
async def health_check():
    auth_healthy = await check_auth_service_health()
    transaction_healthy = await check_transaction_service_health()

    if not auth_healthy or not transaction_healthy:
        raise HTTPException(status_code=503, detail="One or more dependencies are not available")

    return {"status": "healthy"}