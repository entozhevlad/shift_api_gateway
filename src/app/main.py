from datetime import datetime
from typing import Optional
import time
import httpx
from fastapi import Depends, FastAPI, HTTPException, Header, Query,  Request, Response
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/login')

REQUEST_COUNT = Counter('request_count', 'Total request count', ['endpoint', 'http_status'])
REQUEST_DURATION = Histogram('request_duration_seconds', 'Duration of requests in seconds', ['endpoint'])

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


# Настройка ресурса с указанием имени сервиса
resource = Resource.create(attributes={"service.name": "api_gateway"})

# Инициализация трейсера с ресурсом
trace_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(trace_provider)

# Настройка Jaeger Exporter
jaeger_exporter = JaegerExporter(
    agent_host_name='jaeger',  # Jaeger host из docker-compose
    agent_port=6831,           # порт Jaeger для UDP
)

# Создание процессора для отправки трейсингов в Jaeger
span_processor = BatchSpanProcessor(jaeger_exporter)
trace_provider.add_span_processor(span_processor)

# Инструментирование FastAPI
FastAPIInstrumentor.instrument_app(app)

# Инструментирование HTTP-клиентов (например, requests)
RequestsInstrumentor().instrument()

# Завершение работы (shutdown) при завершении приложения
@app.on_event("shutdown")
def shutdown_tracer():
    try:
        trace.get_tracer_provider().shutdown()
    except Exception as e:
        print(f"Ошибка завершения трейсера: {e}")


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Middleware для сбора метрик Prometheus."""
    start_time = time.time()
    response = await call_next(request)
    request_duration = time.time() - start_time

    # Логирование количества запросов по эндпоинтам и статусам
    REQUEST_COUNT.labels(endpoint=request.url.path, http_status=response.status_code).inc()

    # Логирование времени выполнения запросов
    REQUEST_DURATION.labels(endpoint=request.url.path).observe(request_duration)

    return response

# Эндпоинт для получения метрик
@app.get("/metrics")
async def get_metrics():
    """Эндпоинт для получения метрик Prometheus."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


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
    username: str = Query(...),
    password: str = Query(...),
    first_name: Optional[str] = Query(None),
    last_name: Optional[str] = Query(None),
):
    """Регистрация нового пользователя."""
    async with httpx.AsyncClient() as client:
        return await post_request(
            client,
            f'{AUTH_SERVICE_URL}/register',
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
            f'{AUTH_SERVICE_URL}/login',
            data=login_data,
            headers=headers,
        )


@app.post('/transactions/')
async def create_transaction(
    request: TransactionCreateRequest,
    token: str = Header(...)
):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{TRANSACTION_SERVICE_URL}/transaction/transactions/",
                json={'amount': request.amount, 'type': request.type},
                headers= {
                    'token': token,  # Используем 'token' вместо 'Authorization'
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            )
            response.raise_for_status()  # Поднимает исключение для HTTP ошибок
            return response.json()  # Возвращаем JSON-ответ от сервиса транзакций
        except httpx.HTTPStatusError as e:
            # Обработка HTTP ошибок
            raise HTTPException(status_code=e.response.status_code, detail=e.response.json())
        except httpx.RequestError as e:
            # Обработка ошибок запроса
            raise HTTPException(status_code=500, detail=str(e))


@app.post('/transactions/report/')
async def get_transactions_report(
    request: DateRangeRequest,
    token: str = Header(...),
):
    """Получение отчета по транзакциям за указанный временной диапазон."""

    # Преобразование дат в ISO формат
    start_iso = request.start.isoformat()
    end_iso = request.end.isoformat()

    # Создание клиента HTTPX
    async with httpx.AsyncClient() as client:
        try:
            # Отправка запроса к сервису транзакций
            response = await client.post(
                f'{TRANSACTION_SERVICE_URL}/transaction/transactions/report/',
                json={'start': start_iso, 'end': end_iso},
                headers={'token': token}
            )

            # Проверка успешности запроса
            response.raise_for_status()  # Поднимает исключение для HTTP ошибок

            return response.json()  # Возвращаем JSON-ответ от сервиса транзакций
        except httpx.HTTPStatusError as e:
            # Обработка HTTP ошибок
            raise HTTPException(status_code=e.response.status_code, detail=e.response.json())
        except httpx.RequestError as e:
            # Обработка ошибок запроса
            raise HTTPException(status_code=500, detail=str(e))



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
    auth_url = f'{AUTH_SERVICE_URL}/healthz/ready'
    trans_url = f'{TRANSACTION_SERVICE_URL}/transaction/healthz/ready'

    auth_healthy = await check_service_health(auth_url)
    transaction_healthy = await check_service_health(trans_url)

    if not auth_healthy or not transaction_healthy:
        raise HTTPException(
            status_code=HTTP_SERVICE_UNAVAILABLE,
            detail='Один или несколько сервисов недоступны',
        )

    return {'status': 'healthy'}


@app.post('/api/verify')
async def verify_user(token: str = Depends(oauth2_scheme)):
    """Верификация пользователя с проверкой JWT-токена."""
    headers = {'Authorization': f'Bearer {token}'}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f'{AUTH_SERVICE_URL}/verify',
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=exc.response.json().get(DETAIL_KEY, 'Ошибка при верификации'),
            )
