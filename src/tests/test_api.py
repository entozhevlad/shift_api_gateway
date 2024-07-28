import pytest
from fastapi import FastAPI
from httpx import AsyncClient, MockTransport, Request, Response
from src.app.main import app, AUTH_SERVICE_URL, TRANSACTION_SERVICE_URL

@pytest.fixture
def anyio_backend():
    return 'asyncio'

def mock_response(request: Request) -> Response:
    if request.url.path == "/register" and request.method == "POST":
        return Response(200, json={"message": "User registered"})
    if request.url.path == "/login" and request.method == "POST":
        return Response(200, json={"token": "fake-token"})
    if request.url.path == "/verify" and request.method == "POST":
        if request.json()["token"] == "fake-token":
            return Response(200, json={"user": "fake-user"})
        return Response(401, json={"detail": "Invalid or expired token"})
    if request.url.path.startswith("/transactions/") and request.method == "POST":
        if request.headers.get("Authorization") == "Bearer fake-token":
            if request.url.path == "/transactions/report/":
                return Response(200, json={"report": "data"})
            return Response(200, json={"transaction": "created"})
        return Response(401, json={"detail": "Invalid or expired token"})
    return Response(404, json={"detail": "Not found"})

transport = MockTransport(mock_response)

@pytest.mark.anyio
async def test_register():
    async with AsyncClient(app=app, base_url="http://test", transport=transport) as client:
        response = await client.post("/register", json={"username": "user", "password": "pass"})
        assert response.status_code == 200
        assert response.json() == {"message": "User registered"}

@pytest.mark.anyio
async def test_login():
    async with AsyncClient(app=app, base_url="http://test", transport=transport) as client:
        response = await client.post("/login", json={"username": "user", "password": "pass"})
        assert response.status_code == 200
        assert response.json() == {"token": "fake-token"}

@pytest.mark.anyio
async def test_create_transaction():
    async with AsyncClient(app=app, base_url="http://test", transport=transport) as client:
        response = await client.post(
            "/transactions/",
            json={"user_id": "user", "amount": 100.0, "type": "deposit"},
            headers={"Authorization": "Bearer fake-token"}
        )
        assert response.status_code == 200
        assert response.json() == {"transaction": "created"}

@pytest.mark.anyio
async def test_get_transactions_report():
    async with AsyncClient(app=app, base_url="http://test", transport=transport) as client:
        response = await client.post(
            "/transactions/report/",
            json={"start": "2024-01-01", "end": "2024-12-31", "user_id": "user"},
            headers={"Authorization": "Bearer fake-token"}
        )
        assert response.status_code == 200
        assert response.json() == {"report": "data"}

@pytest.mark.anyio
async def test_get_current_user_invalid_token():
    async with AsyncClient(app=app, base_url="http://test", transport=transport) as client:
        response = await client.post(
            "/transactions/",
            json={"user_id": "user", "amount": 100.0, "type": "deposit"},
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401
        assert response.json() == {"detail": "Invalid or expired token"}
