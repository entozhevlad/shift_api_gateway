import pytest
from fastapi.testclient import TestClient
from httpx import Response, Request
from src.app.main import app

client = TestClient(app)


@pytest.fixture
def mock_auth_service(mocker):
    async def mock_post(url, *, data=None, json=None, params=None, headers=None):
        if url == "http://auth_service:82/register":
            if params and params.get("username") == "existing_user":
                return Response(status_code=400, request=Request("POST", url), text='{"detail": "User already exists"}')
            return Response(status_code=200, request=Request("POST", url), text='{"message": "User registered successfully"}')

        if url == "http://auth_service:82/login":
            # Проверка data вместо params
            if data and data.get("username") == "invalid_user":
                return Response(status_code=400, request=Request("POST", url), text='{"detail": "Invalid credentials"}')
            return Response(status_code=200, request=Request("POST", url), text='{"access_token": "valid_token"}')

    mocker.patch('httpx.AsyncClient.post', side_effect=mock_post)


@pytest.fixture
def mock_transaction_service(mocker):
    async def mock_post(url, json=None, params=None):
        if url == "http://transactions_service:83/transaction/transactions/":
            if params and params.get("token") == "invalid_token":
                return Response(status_code=401, text='{"detail": "Invalid token"}')
            return Response(status_code=200, text='{"message": "Transaction created"}')

        if url == "http://transactions_service:83/transaction/transactions/report/":
            return Response(status_code=200, text='{"report": "Some report data"}')

    mocker.patch('httpx.AsyncClient.post', side_effect=mock_post)


@pytest.fixture
def mock_health_check(mocker):
    async def mock_get(url, *args, **kwargs):
        if url == "http://transactions_service:83/transaction/healthz/ready":
            # Создаем корректный объект Request для Response
            request = Request("GET", url)
            return Response(status_code=200, text='{"status": "healthy"}', request=request)
        if url == "http://auth_service:82/healthz/ready":
            # Создаем корректный объект Request для Response
            request = Request("GET", url)
            return Response(status_code=200, text='{"status": "healthy"}', request=request)
        return Response(status_code=404, text='{"detail": "Not Found"}', request=Request("GET", url))

    mocker.patch('httpx.AsyncClient.get', side_effect=mock_get)


def test_register_user_success(mock_auth_service):
    response = client.post("/register", params={"username": "new_user",
                           "password": "password123", "first_name": "Vladislav", "last_name": "Zarubin"})
    assert response.status_code == 200
    assert response.json() == {"message": "User registered successfully"}


def test_register_user_already_exists(mock_auth_service):
    response = client.post(
        "/register", params={"username": "existing_user", "password": "password123"})
    assert response.status_code == 400
    assert response.json() == {"detail": "User already exists"}


def test_login_user_success(mock_auth_service):
    response = client.post(
        "/login", data={"username": "valid_user", "password": "password123"})
    assert response.status_code == 200
    assert response.json() == {"access_token": "valid_token"}


def test_login_user_invalid_credentials(mock_auth_service):
    response = client.post(
        "/login", data={"username": "invalid_user", "password": "password123"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid credentials"}


def test_create_transaction_success(mock_transaction_service):
    response = client.post(
        "/transactions/", json={"amount": 100.0, "type": "debit"}, params={"token": "valid_token"})
    assert response.status_code == 200
    assert response.json() == {"message": "Transaction created"}


def test_create_transaction_invalid_token(mock_transaction_service):
    response = client.post(
        "/transactions/", json={"amount": 100.0, "type": "debit"}, params={"token": "invalid_token"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token"}


def test_get_transactions_report_success(mock_transaction_service):
    response = client.post("/transactions/report/", json={
                           "start": "2024-01-01T00:00:00", "end": "2024-01-31T23:59:59"}, params={"token": "valid_token"})
    assert response.status_code == 200
    assert response.json() == {"report": "Some report data"}


def test_health_check_success(mock_health_check):
    response = client.get("/healthz/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
