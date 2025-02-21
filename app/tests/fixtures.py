import docker
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

import conftest
from app.database import get_db
from app.main import app
from app.models import Base, Like, Tweet, User

# Подключение к Docker
client = docker.from_env()
# Получение контейнера по имени
container = client.containers.get("test_db_container")
# Получение информации о сетевом интерфейсе контейнера
network_info = list(container.attrs["NetworkSettings"]["Networks"].values())[0]
ip_address = network_info["IPAddress"]

TEST_DATABASE_URL = (
    f"postgresql+asyncpg://user:password@{ip_address}:5432/tweet-clone-test"
)

# Создание асинхронного движка и сессии
test_engine = create_async_engine(TEST_DATABASE_URL, echo=True)
TestSessionLocal = sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Переопределение зависимости get_db для тестов
@pytest_asyncio.fixture(scope="module")
async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest_asyncio.fixture(scope="module")
async def async_client(override_get_db):
    conftest.TESTING = True
    async with AsyncClient(
        base_url="http://0.0.0.0:80", transport=ASGITransport(app)
    ) as ac:
        app.dependency_overrides[get_db] = lambda: override_get_db
        yield ac
    conftest.TESTING = False


# Фикстура для очистки базы данных после всех тестов
@pytest_asyncio.fixture(scope="session", autouse=True)
async def cleanup_database():
    # Используем URL тестовой базы данных
    print("TEST_URL----", TEST_DATABASE_URL)
    print("-IP------------------->>>>", ip_address)
    # Удаляем таблицы перед тестами если существуют
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Создаем таблицы перед тестами
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("\n-СОЗДАНА БАЗА------------------->>>>  УСПЕШНО!\n")

    yield  # Выполняем все тесты

    # Удаляем таблицы после завершения всех тестов
    print("\n-ТЕСТЫ------------------->>>> ЗАКОНЧИЛИСЬ удаляем базу\n")
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="module")
async def test_user():
    async with TestSessionLocal() as db:
        user = User(name="User_test", api_key="test")
        db.add(user)
        await db.commit()
        await db.refresh(user)
        yield user


@pytest_asyncio.fixture(scope="module")
async def tweet(override_get_db, test_user):
    async with TestSessionLocal() as db:
        tweet = Tweet(tweet_data="This is a test tweet", author_id=test_user.id)
        db.add(tweet)
        await db.commit()
        await db.refresh(tweet)
        yield tweet


@pytest_asyncio.fixture(scope="module")
async def like_relation(override_get_db, test_user, tweet):
    async with TestSessionLocal() as db:
        like = Like(user_id=test_user.id, tweet_id=tweet.id)
        db.add(like)
        await db.commit()
        await db.refresh(like)
        yield like
