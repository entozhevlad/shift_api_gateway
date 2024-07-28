import httpx
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel

app = FastAPI()

AUTH_SERVICE_URL = "http://shift-python-2024-auth-service:82"
TRANSACTION_SERVICE_URL = "http://shift-python-2024-transaction-service:83"


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


async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(
            status_code=401, detail="Authorization header missing")
    token = authorization.split(
        " ")[1] if " " in authorization else authorization
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{AUTH_SERVICE_URL}/verify", json={"token": token})
        if response.status_code == 200:
            return response.json().get("user")
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@app.post("/register")
async def register(user_credentials: UserCredentials):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{AUTH_SERVICE_URL}/register", json=user_credentials.dict())
        if response.status_code == 200:
            return response.json()
        raise HTTPException(status_code=response.status_code,
                            detail=response.json().get("detail"))


@app.post("/login")
async def login(user_credentials: UserCredentials):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{AUTH_SERVICE_URL}/login", json=user_credentials.dict())
        if response.status_code == 200:
            return response.json()
        raise HTTPException(status_code=response.status_code,
                            detail=response.json().get("detail"))


@app.post("/transactions/")
async def create_transaction(request: TransactionCreateRequest, token: str = Depends(get_current_user)):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{TRANSACTION_SERVICE_URL}/transaction/transactions/", json=request.dict())
        if response.status_code == 200:
            return response.json()
        raise HTTPException(status_code=response.status_code,
                            detail=response.json().get("detail"))


@app.post("/transactions/report/")
async def get_transactions_report(request: DateRangeRequest, token: str = Depends(get_current_user)):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{TRANSACTION_SERVICE_URL}/transaction/transactions/report/", json=request.dict())
        if response.status_code == 200:
            return response.json()
        raise HTTPException(status_code=response.status_code,
                            detail=response.json().get("detail"))
