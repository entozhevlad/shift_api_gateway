from datetime import datetime
from typing import Optional

import httpx
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

app = FastAPI()

# URLs микросервисов
AUTH_SERVICE_URL = 'http://auth_service:82'
TRANSACTION_SERVICE_URL = 'http://transactions_service:83'

HTTP_STATUS_OK = 200
HTTP_SERVICE_UNAVAILABLE = 503

DETAIL_KEY = 'detail'


class TransactionCreateRequest(BaseModel):
    """Модель для создания транзакции."""

    amount: float
    type: str = Field(..., pattern='(debit|credit)')


class DateRangeRequest(BaseModel):
    """Модель для указания временного диапазона."""

    start: datetime = Field(..., description='Начало временного диапазона')
    end: datetime = Field(..., description='Конец временного диапазона')


async def post_request(client: httpx.AsyncClient, url: str, **kwargs):
    """Универсальная функция для выполнения POST-запросов."""
    response = await client.post(url, **kwargs)
    if response.status_code == HTTP_STATUS_OK:
        return response.json()
    raise HTTPException(
        status_code=response.status_code,
        detail=response.json().get(DETAIL_KEY),
    )


@app.post('/register')
async def register(
    username: str = Query(default=None),
    password: str = Query(default=None),
    first_name: Optional[str] = Query(default=None),
    last_name: Optional[str] = Query(default=None),
):
    """Регистрация нового пользователя."""
    async with httpx.AsyncClient() as client:
        return await post_request(
            client,
            '{0}/register'.format(AUTH_SERVICE_URL),
            params={
                'username': username,
                'password': password,
                'first_name': first_name,
                'last_name': last_name,
            },
        )


@app.post('/login')
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Логин пользователя."""
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    login_data = {
        'username': form_data.username,
        'password': form_data.password,
    }
    async with httpx.AsyncClient() as client:
        return await post_request(
            client,
            '{0}/login'.format(AUTH_SERVICE_URL),
            data=login_data,
            headers=headers,
        )


@app.post('/transactions/')
async def create_transaction(
    request: TransactionCreateRequest, token: Optional[str] = None,
):
    """Создание транзакции."""
    async with httpx.AsyncClient() as client:
        return await post_request(
            client,
            '{0}/transaction/transactions/'.format(TRANSACTION_SERVICE_URL),
            json={'amount': request.amount, 'type': request.type},
            params={'token': token},
        )


@app.post('/transactions/report/')
async def get_transactions_report(
    request: DateRangeRequest, token: Optional[str] = None,
):
    """Получение отчета по транзакциям за указанный временной диапазон."""
    start_iso = request.start.isoformat()
    end_iso = request.end.isoformat()

    async with httpx.AsyncClient() as client:
        return await post_request(
            client,
            '{0}/transaction/transactions/report/'.format(
                TRANSACTION_SERVICE_URL,
            ),
            json={'start': start_iso, 'end': end_iso},
            params={'token': token},
        )


async def check_service_health(url: str) -> bool:
    """Универсальная функция проверки состояния сервиса."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response.status_code == HTTP_STATUS_OK
        except httpx.RequestError:
            return False


@app.get('/healthz/ready')
async def health_check():
    """Проверка состояния всех сервисов."""
    auth_url = '{0}/healthz/ready'.format(AUTH_SERVICE_URL)
    trans_url = '{0}/transaction/healthz/ready'.format(TRANSACTION_SERVICE_URL)

    auth_healthy = await check_service_health(auth_url)
    transaction_healthy = await check_service_health(trans_url)

    if not auth_healthy or not transaction_healthy:
        raise HTTPException(
            status_code=HTTP_SERVICE_UNAVAILABLE,
            detail='Один или несколько сервисов недоступны',
        )

    return {'status': 'healthy'}
