import logging

from fastapi import APIRouter, Depends, File, Header, UploadFile
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

import conftest
from app.crud import (
    check_follow_relationship,
    check_like_exists,
    create_follow_relationship,
    create_like,
    create_new_tweet,
    delete_follower_relationship,
    delete_tweet_from_db,
    format_tweet_list,
    format_user_profile_response,
    get_all_tweets,
    get_follower_relationship,
    get_like_relation,
    get_tweet_by_id,
    get_user_by_id_or_api_key,
    remove_like_relation,
    save_file,
    save_media_to_db,
)
from app.database import get_db
from app.schemas import TweetCreate

router = APIRouter()

logging.basicConfig(level=logging.INFO)


@router.post("/api/tweets", description="Создает новый твит")
async def create_tweet(
    tweet: TweetCreate, api_key: str = Header(None), db: AsyncSession = Depends(get_db)
):
    # Найти текущего пользователя по api_key
    if conftest.TESTING:
        api_key = "test"

    current_user = await get_user_by_id_or_api_key(api_key, db)

    logging.info(f"Пробуем создать новый твит для {current_user} в API/TWEETS")
    db_tweet = await create_new_tweet(
        tweet.tweet_data, current_user.id, tweet.tweet_media_ids or [], db
    )
    logging.info(f"Новый твит для {current_user} СОЗДАН!!!")

    return {"result": True, "tweet_id": db_tweet.id}


@router.get("/api/users/me", description="Страница текущего пользователя")
async def get_user_info(
    api_key: str = Header(None), db: AsyncSession = Depends(get_db)
):
    if conftest.TESTING:
        api_key = "test"

    logging.info(f"Получаем юзера по ключу: {api_key}")
    user = await get_user_by_id_or_api_key(api_key, db)

    response = await format_user_profile_response(user)

    return response


@router.get(
    "/api/users/{user_id}", description="Страница пользователя с определённым id"
)
async def get_user_profile(
    user_id: int, api_key: str = Header(None), db: AsyncSession = Depends(get_db)
):
    logging.info(f"Получаем профиль пользователя с ID: {user_id}")
    user = await get_user_by_id_or_api_key(user_id, db)

    logging.info(
        f"Пользователь с ID: {user_id} найден. Формируем ответ для USER/USER_ID"
    )
    response = await format_user_profile_response(user)
    logging.info(f"ВОЗВРАЩАЕМ ИЗ GET/USERS/USER_ID: {response}")

    return response


@router.get("/api/tweets", description="Лента со всеми твитами")
async def get_tweets(api_key: str = Header(None), db: AsyncSession = Depends(get_db)):
    # Получить твиты, связанные с пользователем
    logging.info("ПРОБУЕМ ПОЛУЧИТЬ ТВИТЫ юзеров")
    tweets = await get_all_tweets(db)
    tweet_list = await format_tweet_list(tweets)

    return {"result": True, "tweets": tweet_list}


@router.delete(
    "/api/users/{user_id}/follow",
    description="Отписка от пользователя с определенным id",
)
async def unfollow_user(
    user_id: int, api_key: str = Header(None), db: AsyncSession = Depends(get_db)
):
    # Найти текущего пользователя по api_key
    if conftest.TESTING:
        api_key = "test"

    current_user = await get_user_by_id_or_api_key(api_key, db)

    # Найти пользователя, от которого надо отписаться
    user_to_unfollow = await get_user_by_id_or_api_key(user_id, db)

    # Проверка, не подписан ли уже текущий пользователь на этого
    follower_relationship = await get_follower_relationship(
        current_user.id, user_to_unfollow.id, db
    )

    await delete_follower_relationship(follower_relationship, db)

    return {"result": True}


@router.post(
    "/api/users/{user_id}/follow",
    description="Подписка на пользователя с определенным id",
)
async def follow_user(
    user_id: int, api_key: str = Header(None), db: AsyncSession = Depends(get_db)
):
    if conftest.TESTING:
        api_key = "test"

    # Найти текущего пользователя по api_key
    current_user = await get_user_by_id_or_api_key(api_key, db)

    # Найти пользователя, на которого надо подписаться
    user_to_follow = await get_user_by_id_or_api_key(user_id, db)

    if await check_follow_relationship(current_user.id, user_to_follow.id, db):
        raise HTTPException(status_code=400, detail="Already following this user")
    # Создать запись о подписке
    await create_follow_relationship(current_user.id, user_to_follow.id, db)

    return {"result": True}


@router.delete(
    "/api/tweets/{tweet_id}/likes",
    description="Удаление лайка на  Tweet с определенным id",
)
async def remove_like(
    tweet_id: int, api_key: str = Header(None), db: AsyncSession = Depends(get_db)
):
    if conftest.TESTING:
        api_key = "test"

    # Найти текущего пользователя по api_key
    current_user = await get_user_by_id_or_api_key(api_key, db)

    # Найти лайк для твита и текущего пользователя
    like_relation = await get_like_relation(tweet_id, current_user.id, db)

    # Удалить лайк из базы данных
    await remove_like_relation(like_relation, db)

    return {"result": True}


@router.post(
    "/api/tweets/{tweet_id}/likes",
    description="Лайк на Tweet пользователя с определенным id",
)
async def like_tweet(
    tweet_id: int, api_key: str = Header(None), db: AsyncSession = Depends(get_db)
):
    if conftest.TESTING:
        api_key = "test"

    # Найти текущего пользователя по api_key
    current_user = await get_user_by_id_or_api_key(api_key, db)

    # Проверка, не поставил ли уже текущий пользователь лайк на этот твит
    if await check_like_exists(tweet_id, current_user.id, db):
        raise HTTPException(status_code=400, detail="Already liked this tweet")

    # Создать запись о лайке
    await create_like(tweet_id, current_user.id, db)

    return {"result": True}


@router.delete(
    "/api/tweets/{tweet_id}", description="Удаляет твит по его идентификатору"
)
async def delete_tweet(
    tweet_id: int, api_key: str = Header(None), db: AsyncSession = Depends(get_db)
):
    if conftest.TESTING:
        api_key = "test"

    # Найти текущего пользователя по api_key
    current_user = await get_user_by_id_or_api_key(api_key, db)

    # Найти твит по его id
    tweet = await get_tweet_by_id(tweet_id, db)

    # Проверить, что твит принадлежит текущему пользователю
    if tweet.author_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="You can only delete your own tweets"
        )

    # Удалить твит из базы данных
    await delete_tweet_from_db(tweet, db)

    return {"result": True}


@router.post("/api/medias", description="Добавление медиа контента к твиту")
async def upload_media(
    api_key: str = Header(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if conftest.TESTING:
        api_key = "test"

    # Найти текущего пользователя по api_key
    current_user = await get_user_by_id_or_api_key(api_key, db)

    # Проверить и сохранить файл
    media_filename = await save_file(file)

    # Сохранить информацию о медиа в базе данных
    new_media = await save_media_to_db(media_filename, current_user.id, db)

    return {"result": True, "media_id": new_media.id}
