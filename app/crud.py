import os
import shutil
import uuid

from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

import conftest

from .models import Follower, Like, Media, Tweet, User


async def create_new_tweet(
    tweet_data: str, author_id: int, media_ids: list, db: AsyncSession
) -> Tweet:
    """
    Создание нового твита
    :param tweet_data: Текст твита
    :param author_id: ID автора твита
    :param media_ids: Список ID медиафайлов, прикрепленных к твиту
    :param db: Асинхронная сессия базы данных
    :return: Объект нового твита
    """
    # Создаем новый твит
    db_tweet = Tweet(tweet_data=tweet_data, author_id=author_id)

    # Проверка и добавление медиа-идентификаторов, если они существуют
    if media_ids:
        media_query = await db.execute(select(Media).filter(Media.id.in_(media_ids)))
        media_items = media_query.scalars().all()
        if len(media_items) != len(media_ids):
            raise HTTPException(
                status_code=404, detail="One or more media IDs not found"
            )
        db_tweet.media_items = media_items

    db.add(db_tweet)
    await db.commit()
    await db.refresh(db_tweet)

    return db_tweet


async def get_user_by_id_or_api_key(param: int | str, db: AsyncSession) -> User:
    """
    Находим данные юзера по его id или другому параметру
    :param param: id или другой параметр (например, username)
    :param db: сессия БД
    :return: объект пользователя
    """
    if isinstance(param, int):
        filter_condition = User.id == param
    else:
        filter_condition = User.api_key == param

    result = await db.execute(
        select(User)
        .options(
            joinedload(User.followers).joinedload(Follower.follower),
            joinedload(User.following).joinedload(Follower.followed),
        )
        .filter(filter_condition)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


async def format_user_profile_response(user: User) -> dict:
    """
    Форматирование данных профиля юзера
    :param user: Объект пользователя
    :return: Словарь с отформатированными данными профиля
    """
    user_profile = {
        "result": "true",
        "user": {
            "id": user.id,
            "name": user.name,
            "followers": [
                {"id": follow.follower.id, "name": follow.follower.name}
                for follow in user.followers
            ],
            "following": [
                {"id": follow.followed.id, "name": follow.followed.name}
                for follow in user.following
            ],
        },
    }
    return user_profile


async def get_all_tweets(db: AsyncSession) -> list:
    """
    Получение списка всех твитов
    :param db: Асинхронная сессия базы данных
    :return: Список всех твитов
    """
    result = await db.execute(
        select(Tweet).options(
            joinedload(Tweet.author),
            joinedload(Tweet.media_items),
            joinedload(Tweet.likes).joinedload(
                Like.user
            ),  # Полный путь от Tweet до Like и User
        )
    )
    tweets = result.scalars().unique().all()
    return tweets


async def format_tweet_list(tweets: list) -> list:
    """
    Форматирование данных всех твитов
    :param tweets: Список объектов твитов
    :return: Список отформатированных данных твитов
    """
    tweet_list = []
    for tweet in tweets:
        tweet_list.append(
            {
                "id": tweet.id,
                "content": tweet.tweet_data,  # Используем правильное поле
                "attachments": [
                    f"http://0.0.0.0/media/{attachment.filename}"
                    for attachment in tweet.media_items or []
                    if attachment.filename.lower().endswith(
                        (".png", ".jpg", ".jpeg", ".gif")
                    )
                ],
                "author": {"id": tweet.author.id, "name": tweet.author.name},
                "likes": [
                    {"user_id": like.user.id, "name": like.user.name}
                    for like in tweet.likes or []
                ],
            }
        )

    return tweet_list


async def get_follower_relationship(
    current_user_id: int, user_to_unfollow_id: int, db: AsyncSession
) -> Follower:
    """
    Нахождение юзера для отписки
    :param current_user_id: ID текущего пользователя
    :param user_to_unfollow_id: ID пользователя, от которого нужно отписаться
    :param db: Асинхронная сессия базы данных
    :return: Объект, представляющий связь подписчика
    """
    result = await db.execute(
        select(Follower)
        .options(joinedload(Follower.follower), joinedload(Follower.followed))
        .filter(
            Follower.follower_id == current_user_id,
            Follower.followed_id == user_to_unfollow_id,
        )
    )
    follower_relationship = result.scalars().first()
    if not follower_relationship:
        raise HTTPException(status_code=404, detail="Follower relationship not found")

    return follower_relationship


async def delete_follower_relationship(
    follower_relationship: Follower, db: AsyncSession
):
    """
    Удаление юзера из подписок
    :param follower_relationship: Объект, представляющий связь подписчика
    :param db: Асинхронная сессия базы данных
    :return: Ничего не возвращает
    """
    await db.delete(follower_relationship)
    await db.commit()


async def check_follow_relationship(
    current_user_id: int, user_to_follow_id: int, db: AsyncSession
) -> bool:
    """
    Проверка существования подписки между пользователями
    :param current_user_id: ID текущего пользователя
    :param user_to_follow_id: ID пользователя, на которого проверяется подписка
    :param db: Асинхронная сессия базы данных
    :return: True, если подписка существует, иначе False
    """
    result = await db.execute(
        select(Follower)
        .options(joinedload(Follower.follower), joinedload(Follower.followed))
        .filter(
            Follower.follower_id == current_user_id,
            Follower.followed_id == user_to_follow_id,
        )
    )
    follow_relation = result.scalars().first()
    return follow_relation is not None


async def create_follow_relationship(
    current_user_id: int, user_to_follow_id: int, db: AsyncSession
):
    """
    Создание подписки между пользователями
    :param current_user_id: ID текущего пользователя
    :param user_to_follow_id: ID пользователя, на которого осуществляется подписка
    :param db: Асинхронная сессия базы данных
    :return: Ничего не возвращает
    """
    new_follow = Follower(follower_id=current_user_id, followed_id=user_to_follow_id)
    db.add(new_follow)
    await db.commit()


async def get_like_relation(tweet_id: int, user_id: int, db: AsyncSession) -> Like:
    """
    Получение информации о лайке пользователя на твит
    :param tweet_id: ID твита
    :param user_id: ID пользователя
    :param db: Асинхронная сессия базы данных
    :return: Объект, представляющий отношение лайка
    """
    result = await db.execute(
        select(Like).filter(Like.tweet_id == tweet_id, Like.user_id == user_id)
    )
    like_relation = result.scalars().first()
    if not like_relation:
        raise HTTPException(status_code=404, detail="Like not found")

    return like_relation


async def remove_like_relation(like_relation: Like, db: AsyncSession):
    """
    Удаление лайка из твита
    :param like_relation: Объект, представляющий отношение лайка
    :param db: Асинхронная сессия базы данных
    :return: Ничего не возвращает
    """
    await db.delete(like_relation)
    await db.commit()


async def get_tweet_by_id(tweet_id: int, db: AsyncSession) -> Tweet:
    """
    Получение твита по его идентификатору
    :param tweet_id:  ID твита
    :param db: Асинхронная сессия базы данных
    :return: Объект твита
    """
    result = await db.execute(
        select(Tweet).options(joinedload(Tweet.author)).filter(Tweet.id == tweet_id)
    )
    tweet = result.scalars().first()
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")

    return tweet


async def check_like_exists(tweet_id: int, user_id: int, db: AsyncSession) -> bool:
    """
    Проверка наличия лайка пользователя на твит
    :param tweet_id: ID твита
    :param user_id: ID пользователя
    :param db: Асинхронная сессия базы данных
    :return: True, если лайк существует, иначе False
    """
    result = await db.execute(
        select(Like).filter(Like.tweet_id == tweet_id, Like.user_id == user_id)
    )
    like_relation = result.scalars().first()

    return like_relation is not None


async def create_like(tweet_id: int, user_id: int, db: AsyncSession):
    """
    Создание лайка на твит
    :param tweet_id: ID твита
    :param user_id: ID пользователя
    :param db: Асинхронная сессия базы данных
    :return: Ничего не возвращает
    """
    new_like = Like(tweet_id=tweet_id, user_id=user_id)
    db.add(new_like)
    await db.commit()


async def delete_tweet_from_db(tweet: Tweet, db: AsyncSession):
    """
    Удаление твита из базы данных
    :param tweet: Объект твита
    :param db: Асинхронная сессия базы данных
    :return: Ничего не возвращает
    """
    await db.delete(tweet)
    await db.commit()


async def save_file(file: UploadFile) -> str:
    """
    Обработка и сохранение загруженного медиафайла для твита
    :param file: Объект загруженного файла (UploadFile)
    :return: Путь к сохраненному файлу
    """
    file_extension = os.path.splitext(file.filename)[1]
    media_filename = f"{uuid.uuid4()}{file_extension}"
    media_path = f"/app/media/{media_filename}"
    if conftest.TESTING:
        media_path = f"/tmp/media/{media_filename}"  # Используем временную директорию
    # Создаем директорию, если она не существует
    os.makedirs(os.path.dirname(media_path), exist_ok=True)

    with open(media_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return media_filename


async def save_media_to_db(
    media_filename: str, user_id: int, db: AsyncSession
) -> Media:
    """
    Сохранение медиафайла в базе данных
    :param media_filename: Имя файла медиа
    :param user_id: ID пользователя
    :param db: Асинхронная сессия базы данных
    :return: Объект медиа
    """
    new_media = Media(filename=media_filename, user_id=user_id)
    db.add(new_media)
    await db.commit()
    return new_media
