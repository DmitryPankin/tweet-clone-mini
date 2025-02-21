#!/usr/bin/env python3
import logging

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.database import DATABASE_URL
from app.models import Base, Tweet, User

# Создание асинхронного движка и сессии
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

logging.basicConfig(level=logging.INFO)


async def init_db():
    async with engine.begin() as conn:
        # Удаление существующих таблиц
        await conn.run_sync(Base.metadata.drop_all)
        # Создание новых таблиц
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        users = [
            User(name="User_1", api_key="test", followers=[], following=[]),
            User(name="User_2", api_key="test2", followers=[], following=[]),
            User(name="User_3", api_key="test3", followers=[], following=[]),
            # Добавьте больше пользователей по необходимости
        ]

        tweets = [
            Tweet(tweet_data="Я ЮЗЕР 2", author_id=2),
            Tweet(tweet_data="Я ТОЖЕ ЮЗЕР 2", author_id=2),
            Tweet(tweet_data="Я ЮЗЕР 3", author_id=3),
            # Добавьте больше пользователей по необходимости
        ]

        for user in users:
            db.add(user)

        for tweet in tweets:
            db.add(tweet)

        await db.commit()

        for user in users:
            await db.refresh(user)

        for tweet in tweets:
            await db.refresh(tweet)

        # Логирование созданных пользователей
        for user in users:
            logging.info(
                f"Создан пользователь: {user.name} с API ключом: {user.api_key}"
            )

        for tweet in tweets:
            logging.info(f"Создан tweet для юзера {tweet.author_id} ")


if __name__ == "__main__":
    import asyncio

    asyncio.run(init_db())
