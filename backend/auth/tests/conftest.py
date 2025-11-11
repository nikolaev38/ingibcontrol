import asyncio, pytest
from fastapi.testclient import TestClient
from core.models.db_connect import db_fastapi_connect
from main import app

# Фикстура для синхронного клиента
@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture(scope='session')
def event_loop():
    """Создание event_loop с уровнем сессии (session) вместо function."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Фикстура для получения сессионного объекта
@pytest.fixture
async def async_session():
    # Можно использовать ваш scoped_session_dependency
    generator = db_fastapi_connect.scoped_session_dependency()
    session = await generator.__anext__()
    try:
        yield session
    finally:
        await session.close()


