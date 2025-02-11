#!/usr/bin/env python3

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from app.models import User, Base
from app.database import DATABASE_URL

# Создание асинхронного движка и сессии
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    async with engine.begin() as conn:
        # Создание таблиц синхронно в контексте асинхронной задачи
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        # Поиск пользователя с api_key "test"
        result = await db.execute(select(User).filter(User.api_key == "test3"))
        user = result.scalars().first()
        if user:
            await db.delete(user)
            await db.commit()

        # Создание нового пользователя
        test_user = User(
            name="User3",
            api_key="test3",
            followers=[],
            following=[]
        )
        db.add(test_user)
        await db.commit()
        await db.refresh(test_user)

if __name__ == "__main__":
    asyncio.run(init_db())
