import pytest
from httpx import AsyncClient, Response
from fastapi import FastAPI
from src.app.main import app, get_redis
from redis.asyncio import Redis
from unittest.mock import AsyncMock
import respx

# Фикстура для асинхронного клиента


@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

# Фикстура для мока Redis


@pytest.fixture
def mock_redis():
    return AsyncMock(spec=Redis)

# Заменяем зависимость Redis на мок


@pytest.fixture(autouse=True)
def override_redis_dependency(mock_redis):
    app.dependency_overrides[get_redis] = lambda: mock_redis

# Тестирование регистрации пользователя


@pytest.mark.asyncio
async def test_register_user(async_client, mock_redis):
    with respx.mock(base_url="http://auth_service:82") as mock:
        mock.post("/register").mock(return_value=Response(200,
                                                          json={"status": "success"}))
        response = await async_client.post(
            "/register",
            json={"username": "testuser", "password": "password123",
                  "first_name": "Test", "last_name": "User"}
        )
        assert response.status_code == 200
        assert response.json() == {"status": "success"}

# Тестирование логина пользователя


@pytest.mark.asyncio
async def test_login_user(async_client):
    with respx.mock(base_url="http://auth_service:82") as mock:
        mock.post("/login").mock(return_value=Response(200,
                                                       json={"access_token": "fake_token"}))
        response = await async_client.post(
            "/login",
            data={"username": "testuser", "password": "password123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 200
        assert response.json() == {"access_token": "fake_token"}

# Тестирование создания транзакции


@pytest.mark.asyncio
async def test_create_transaction(async_client, mock_redis):
    mock_redis.get.return_value = None
    with respx.mock(base_url="http://transactions_service:83") as mock:
        mock.post("/transactions/").mock(return_value=Response(200,
                                                               json={"status": "transaction created"}))
        response = await async_client.post(
            "/transactions/",
            json={"amount": 100.0, "type": "debit"},
            headers={"Authorization": "Bearer fake_token"}
        )
        assert response.status_code == 200
        assert response.json() == {"status": "transaction created"}
        mock_redis.setex.assert_called_once()

# Тестирование получения отчета по транзакциям


@pytest.mark.asyncio
async def test_get_transactions_report(async_client, mock_redis):
    mock_redis.get.return_value = None
    with respx.mock(base_url="http://transactions_service:83") as mock:
        mock.post("/transactions/report/").mock(return_value=Response(200,
                                                                      json={"report": "some data"}))
        response = await async_client.post(
            "/transactions/report/",
            json={"start": "2024-01-01T00:00:00", "end": "2024-01-31T23:59:59"},
            headers={"Authorization": "Bearer fake_token"}
        )
        assert response.status_code == 200
        assert response.json() == {"report": "some data"}
        mock_redis.setex.assert_called_once()

# Тестирование health check


@pytest.mark.asyncio
async def test_health_check(async_client):
    with respx.mock(base_url="http://auth_service:82") as mock_auth, \
            respx.mock(base_url="http://transactions_service:83") as mock_trans:
        mock_auth.get("/healthz/ready").mock(return_value=Response(200,
                                                                   json={"status": "healthy"}))
        mock_trans.get("/healthz/ready").mock(return_value=Response(200,
                                                                    json={"status": "healthy"}))
        response = await async_client.get("/healthz/ready")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
