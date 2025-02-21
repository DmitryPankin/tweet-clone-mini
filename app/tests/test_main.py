from io import BytesIO

import pytest
from fastapi import UploadFile

from .fixtures import (
    async_client,
    cleanup_database,
    like_relation,
    override_get_db,
    test_user,
    tweet,
)


@pytest.mark.asyncio
async def test_get_tweets(async_client):
    response = await async_client.get("/api/tweets")
    print("--->>>>>>>>>", response.json())

    assert response.status_code == 200
    assert response.json()["result"] is True


@pytest.mark.asyncio
async def test_add_tweet(async_client, test_user):
    tweet_data = {"tweet_data": "This is a test tweet"}
    response = await async_client.post(
        "/api/tweets",
        json=tweet_data,
    )
    print("--->>>>>>>>>", response.json())

    assert response.status_code == 200
    assert response.json()["result"] is True
    assert response.json()["tweet_id"] == 1


@pytest.mark.asyncio
async def test_get_user_info(async_client, test_user):
    response = await async_client.get("/api/users/me")
    print("--->>>>>>>>>", response.json())

    assert response.status_code == 200
    assert response.json()["result"] == "true"
    assert response.json()["user"]["name"] == "User_test"


@pytest.mark.asyncio
async def test_get_user_profile(async_client, test_user):
    response = await async_client.get(f"/api/users/{test_user.id}")

    print("--->>>>>>>>>\n", response.json())

    assert response.status_code == 200
    assert response.json()["user"]["name"] == "User_test"


# Тест для маршрута unfollow_user
@pytest.mark.asyncio
async def test_unfollow_user(async_client, test_user):
    # Сначала подписываемся на пользователя
    response = await async_client.post(f"/api/users/{test_user.id}/follow")
    assert response.status_code == 200

    # Теперь отписываемся от пользователя
    response = await async_client.delete(f"/api/users/{test_user.id}/follow")
    print("--->>>>>>>>>", response.json())

    assert response.status_code == 200
    assert response.json()["result"] is True


@pytest.mark.asyncio
async def test_like_tweet(async_client, tweet):

    response = await async_client.post(f"/api/tweets/{tweet.id}/likes")
    print("--->>>>>>>>>", response.json())

    assert response.status_code == 200
    assert response.json()["result"] is True


@pytest.mark.asyncio
async def test_remove_like(async_client, like_relation, tweet, test_user):

    # удаляем лайк
    response = await async_client.delete(f"/api/tweets/{tweet.id}/likes")
    print("--->>>>>>>>>", response.json())

    assert response.status_code == 200
    assert response.json()["result"] is True


@pytest.mark.asyncio
async def test_delete_tweet(async_client, tweet):

    response = await async_client.delete(f"/api/tweets/{tweet.id}")
    print("--->>>>>>>>>", response.json())

    assert response.status_code == 200
    assert response.json()["result"] is True


@pytest.mark.asyncio
async def test_upload_media(async_client, test_user):
    # Создаем объект UploadFile для теста
    file_content = b"test content"
    file = UploadFile(filename="test_file.jpg", file=BytesIO(file_content))

    # Данные для загрузки
    files = {"file": (file.filename, file.file, "multipart/form-data")}

    # Загрузка медиа-файла
    response = await async_client.post("/api/medias", files=files)
    print("--->>>>>>>>>", response.json())

    # Проверка статуса и результата
    assert response.status_code == 200
    assert response.json() == {"result": True, "media_id": 1}
