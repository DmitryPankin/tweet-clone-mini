import os
import shutil
import uuid
import logging

from fastapi import APIRouter, HTTPException, Depends, Request, UploadFile, File, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models import Tweet, User, Media, Follower
from app.schemas import TweetCreate

router = APIRouter()
logging.basicConfig(level=logging.INFO)

@router.get("/")
async def read_root():
    return {"message": "Welcome to the API"}


@router.post("/api/tweets")
async def create_tweet(tweet: TweetCreate, request: Request, db: AsyncSession = Depends(get_db)):
    api_key = request.headers.get("api-key")
    if not api_key:
        raise HTTPException(status_code=400, detail="API key missing")

    # Найти текущего пользователя по api_key
    result = await db.execute(
        select(User).options(joinedload(User.followers),
                             joinedload(User.following)).filter(User.api_key == api_key)
    )
    current_user = result.scalars().first()
    if not current_user:
        raise HTTPException(status_code=403, detail="Invalid API key")

    # Создать новый твит
    db_tweet = Tweet(tweet_data=tweet.tweet_data, author_id=current_user.id)

    # Проверка и добавление медиа-идентификаторов, если они существуют
    if tweet.tweet_media_ids:
        media_query = await db.execute(select(Media).filter(Media.id.in_(tweet.tweet_media_ids)))
        media_items = media_query.scalars().all()
        if len(media_items) != len(tweet.tweet_media_ids):
            raise HTTPException(status_code=404, detail="One or more media IDs not found")
        db_tweet.media_items = media_items

    db.add(db_tweet)
    await db.commit()
    await db.refresh(db_tweet)

    return {
        "result": True,
        "tweet_id": db_tweet.id
    }


@router.get("/api/users/me")
async def get_user_info(api_key: str = Header(None), db: AsyncSession = Depends(get_db)):

    # api_key = request.headers.get("api_key")
    logging.info(f"Получаем api_key запроса из Heders: {api_key}")
    if not api_key:
        raise HTTPException(status_code=400, detail="API key missing")

    # Найти текущего пользователя по api_key с предварительной загрузкой связанных объектов
    result = await db.execute(
        select(User).options(
            joinedload(User.followers),
            joinedload(User.following)
        ).filter(User.api_key == api_key)
    )

    user = result.scalars().first()
    logging.info(f"Получен user  по api_key : {user}")
    if not user:
        logging.info(f"User {user} не найден!!!!")
        raise HTTPException(status_code=404, detail="User not found")


    return {
        "id": user.id,
        "name": user.name,
        "followers": [{"id": follower.id, "name": follower.name} for follower in user.followers],
        "following": [{"id": following.id, "name": following.name} for following in user.following]
    }



@router.get("/api/users/{user_id}")
async def get_user_profile(user_id: int, db: AsyncSession = Depends(get_db)):
    logging.info(f"Получаем профиль пользователя с ID: {user_id}")

    result = await db.execute(
        select(User).options(joinedload(User.followers),
                             joinedload(User.following)).filter(User.id == user_id)
    )
    logging.info(f"Запрос выполнен, результаты: {result}")

    user = result.scalars().first()
    if not user:
        logging.error(f"Пользователь с ID: {user_id} не найден")
        raise HTTPException(status_code=404, detail="User not found")

    logging.info(f"Пользователь с ID: {user_id} найден. Формируем ответ")

    return {
        "result": "true",
        "user": {
            "id": user.id,
            "name": user.name,
            "followers": [{"id": follower.id, "name": follower.name} for follower in user.followers],
            "following": [{"id": following.id, "name": following.name} for following in user.following]
        }
    }


@router.get("/api/tweets")
async def get_tweets(request: Request, db: AsyncSession = Depends(get_db)):
    logging.info(f"Заголовки запроса: {request.headers}")

    api_key = request.headers.get("api-key")
    logging.info(f"API ключ: {api_key}")
    if not api_key:
        raise HTTPException(status_code=400, detail="API key missing")

    # Найти пользователя по api_key
    result = await db.execute(
        select(User).options(joinedload(User.followers),
                        joinedload(User.following)).filter(User.api_key == api_key)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=403, detail="Invalid API key")

    # Получить твиты, связанные с пользователем
    result = await db.execute(
        select(Tweet).options(joinedload(Tweet.author)).filter(Tweet.author_id == user.id)
    )
    tweets = result.scalars().all()

    # Форматируем данные для ответа
    tweet_list = []
    for tweet in tweets:
        tweet_list.append({
            "id": tweet.id,
            "content": tweet.tweet_data,  # Используем правильное поле
            "attachments": [attachment.link for attachment in tweet.media_items],
            "author": {
                "id": tweet.author.id,
                "name": tweet.author.name
            },
            "likes": [{"user_id": like.user_id, "name": like.user.name} for like in tweet.likes]
        })

    return {
        "result": True,
        "tweets": tweet_list
    }

@router.delete("/api/users/{user_id}/follow")
async def unfollow_user(user_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    api_key = request.headers.get("api-key")
    if not api_key:
        raise HTTPException(status_code=400, detail="API key missing")

    # Найти текущего пользователя по api_key
    result = await db.execute(
        select(User).options(joinedload(User.followers),
                             joinedload(User.following)).filter(User.api_key == api_key)
    )
    current_user = result.scalars().first()
    if not current_user:
        raise HTTPException(status_code=403, detail="Invalid API key")

    # Найти пользователя, на которого отменяется подписка
    result = await db.execute(
        select(User).options(joinedload(User.followers),
                             joinedload(User.following)).filter(User.id == user_id)
    )
    user_to_unfollow = result.scalars().first()
    if not user_to_unfollow:
        raise HTTPException(status_code=404, detail="User not found")

    # Удалить запись о подписке из базы данных
    result = await db.execute(
        select(Follower).options(joinedload(Follower.follower),
                                         joinedload(Follower.followed)).filter(
             Follower.follower_id == current_user.id,
                     Follower.followed_id == user_to_unfollow.id)
    )
    follower_relationship = result.scalars().first()
    if not follower_relationship:
        raise HTTPException(status_code=404, detail="Relationship not found")

    await db.delete(follower_relationship)
    await db.commit()

    return {
        "result": True
    }


@router.post("/api/users/{user_id}/follow")
async def follow_user(user_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    api_key = request.headers.get("api-key")
    if not api_key:
        raise HTTPException(status_code=400, detail="API key missing")

    # Найти текущего пользователя по api_key
    result = await db.execute(
        select(User).options(joinedload(User.followers),
                             joinedload(User.following)).filter(User.api_key == api_key)
    )
    current_user = result.scalars().first()
    if not current_user:
        raise HTTPException(status_code=403, detail="Invalid API key")

    # Найти пользователя, на которого надо подписаться
    result = await db.execute(
        select(User).options(joinedload(User.followers),
                             joinedload(User.following)).filter(User.id == user_id)
    )
    user_to_follow = result.scalars().first()
    if not user_to_follow:
        raise HTTPException(status_code=404, detail="User not found")

    # Проверка, не подписан ли уже текущий пользователь на этого
    result = await db.execute(
        select(Follower).options(joinedload(Follower.follower), joinedload(Follower.followed))
        .filter(Follower.follower_id == current_user.id,
                        Follower.followed_id == user_to_follow.id)
    )
    follow_relation = result.scalars().first()
    if follow_relation:
        raise HTTPException(status_code=400, detail="Already following this user")

        # Создать запись о подписке
    new_follow = Follower(follower_id=current_user.id, followed_id=user_to_follow.id)

    db.add(new_follow)
    await db.commit()

    return {
        "result": True
    }


@router.delete("/api/tweets/{tweet_id}/likes")
async def remove_like(tweet_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    api_key = request.headers.get("api-key")
    if not api_key:
        raise HTTPException(status_code=400, detail="API key missing")

    # Найти текущего пользователя по api_key
    result = await db.execute(
        select(User).options(joinedload(User.followers),
                             joinedload(User.following)).filter(User.api_key == api_key)
    )
    current_user = result.scalars().first()
    if not current_user:
        raise HTTPException(status_code=403, detail="Invalid API key")

    # Найти лайк для твита и текущего пользователя
    result = await db.execute(
        select(Tweet).options(joinedload(Tweet.tweet),
                                  joinedload(Tweet.user))
        .filter(Tweet.tweet_id == tweet_id,
                Tweet.user_id == current_user.id)
    )
    like_relation = result.scalars().first()
    if not like_relation:
        raise HTTPException(status_code=404, detail="Like not found")

    # Удалить лайк из базы данных
    await db.delete(like_relation)
    await db.commit()

    return {
        "result": True
    }


@router.post("/api/tweets/{tweet_id}/likes")
async def like_tweet(tweet_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    api_key = request.headers.get("api-key")
    if not api_key:
        raise HTTPException(status_code=400, detail="API key missing")

    # Найти текущего пользователя по api_key
    result = await db.execute(
        select(User).options(joinedload(User.followers),
                             joinedload(User.following)).filter(User.api_key == api_key)
    )
    current_user = result.scalars().first()
    if not current_user:
        raise HTTPException(status_code=403, detail="Invalid API key")

    # Проверка, не поставил ли уже текущий пользователь лайк на этот твит
    result = await db.execute(
        select(Tweet).options(joinedload(Tweet.tweet),
                                  joinedload(Tweet.user))
        .filter(Tweet.tweet_id == tweet_id,
                Tweet.user_id == current_user.id)
    )
    like_relation = result.scalars().first()
    if like_relation:
        raise HTTPException(status_code=400, detail="Already liked this tweet")

    # Создать запись о лайке
    new_like = Tweet(tweet_id=tweet_id, user_id=current_user.id)
    db.add(new_like)
    await db.commit()

    return {
        "result": True
    }


@router.delete("/api/tweets/{tweet_id}")
async def delete_tweet(tweet_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    api_key = request.headers.get("api-key")
    if not api_key:
        raise HTTPException(status_code=400, detail="API key missing")

    # Найти текущего пользователя по api_key
    result = await db.execute(
        select(User).options(joinedload(User.followers),
                             joinedload(User.following)).filter(User.api_key == api_key)
    )
    current_user = result.scalars().first()
    if not current_user:
        raise HTTPException(status_code=403, detail="Invalid API key")

    # Найти твит по его id
    result = await db.execute(
        select(Tweet).options(joinedload(Tweet.author)).filter(Tweet.id == tweet_id)
    )
    tweet = result.scalars().first()
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")

    # Проверить, что твит принадлежит текущему пользователю
    if tweet.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own tweets")

    # Удалить твит из базы данных
    await db.delete(tweet)
    await db.commit()

    return {
        "result": True
    }


@router.post("/api/medias")
async def upload_media(request: Request, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    api_key = request.headers.get("api-key")
    if not api_key:
        raise HTTPException(status_code=400, detail="API key missing")

    # Найти текущего пользователя по api_key
    result = await db.execute(
        select(User).options(joinedload(User.followers),
                             joinedload(User.following)).filter(User.api_key == api_key)
    )
    current_user = result.scalars().first()
    if not current_user:
        raise HTTPException(status_code=403, detail="Invalid API key")

    # Проверить и сохранить файл
    file_extension = os.path.splitext(file.filename)[1]
    media_id = str(uuid.uuid4())
    media_filename = f"{media_id}{file_extension}"
    media_path = f"/app/media/{media_filename}"

    with open(media_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Сохранить информацию о медиа в базе данных
    new_media = Media(id=media_id, filename=media_filename, user_id=current_user.id)
    db.add(new_media)
    await db.commit()

    return {
        "result": True,
        "media_id": media_id
    }
