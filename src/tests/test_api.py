import pytest
from fastapi.testclient import TestClient
from myapp import app  # Импортируйте ваш FastAPI объект

client = TestClient(app)

# Мокируем успешное состояние сервисов
@pytest.fixture
def mock_services(mocker):
    mocker.patch("httpx.AsyncClient.get", side_effect=lambda url: {
        "http://auth_service:82/healthz/ready": {"status": "healthy"},
        "http://transactions_service:83/healthz/ready": {"status": "healthy"}
    }.get(url, {}))

def test_health_check_healthy(mock_services):
    response = client.get("/healthz/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

# Мокируем неуспешное состояние одного из сервисов
@pytest.fixture
def mock_services_with_failure(mocker):
    mocker.patch("httpx.AsyncClient.get", side_effect=lambda url: {
        "http://auth_service:82/healthz/ready": {"status": "healthy"},
        "http://transactions_service:83/healthz/ready": None  # Имитация ошибки
    }.get(url, {}))

def test_health_check_with_failure(mock_services_with_failure):
    response = client.get("/healthz/ready")
    assert response.status_code == 503
    assert response.json() == {"detail": "One or more dependencies are not available"}

# Мокируем неуспешное состояние обоих сервисов
@pytest.fixture
def mock_services_with_all_failures(mocker):
    mocker.patch("httpx.AsyncClient.get", side_effect=lambda url: {
        "http://auth_service:82/healthz/ready": None,  # Имитация ошибки
        "http://transactions_service:83/healthz/ready": None  # Имитация ошибки
    }.get(url, {}))

def test_health_check_with_all_failures(mock_services_with_all_failures):
    response = client.get("/healthz/ready")
    assert response.status_code == 503
    assert response.json() == {"detail": "One or more dependencies are not available"}
