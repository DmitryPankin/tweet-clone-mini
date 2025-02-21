# from pydantic import BaseModel
# from typing import List, Optional
#
# class TweetBase(BaseModel):
#     tweet_data: str
#     tweet_media_ids: Optional[List[int]] = None
#
# class TweetCreate(TweetBase):
#     pass
#
# class Tweet(TweetBase):
#     id: int
#     likes: List['TweetLike']
#
#     class Config:
#         from_attributes = True
#
# class UserBase(BaseModel):
#     name: str
#     api_key: str
#
# class UserCreate(UserBase):
#     pass
#
# class User(UserBase):
#     id: int
#     followers: Optional[List[int]] = None  # Список id подписчиков
#     following: Optional[List[int]] = None  # Список id подписок
#     likes: List['TweetLike']
#
#     class Config:
#         from_attributes = True
#
# class LikeBase(BaseModel):
#     user_id: int
#     tweet_id: int
#
# class LikeCreate(LikeBase):
#     pass
#
# class Like(LikeBase):
#     id: int
#
#     class Config:
#         from_attributes = True
#
# class FollowerBase(BaseModel):
#     follower_id: int
#     followed_id: int
#
# class FollowerCreate(FollowerBase):
#     pass
#
# class Follower(FollowerBase):
#     id: int
#
#     class Config:
#         from_attributes = True
#
# class TweetLikeBase(BaseModel):
#     user_id: int
#     tweet_id: int
#
# class TweetLikeCreate(TweetLikeBase):
#     pass
#
# class TweetLike(TweetLikeBase):
#     id: int
#
#     class Config:
#         from_attributes = True
#
# class MediaBase(BaseModel):
#     filename: str
#     user_id: int
#     tweet_id: Optional[int] = None
#
# class MediaCreate(MediaBase):
#     pass
#
# class Media(MediaBase):
#     id: int
#
#     class Config:
#         from_attributes = True


from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class TweetBase(BaseModel):
    tweet_data: str
    tweet_media_ids: Optional[List[int]] = None


class TweetCreate(TweetBase):
    pass


class Tweet(TweetBase):
    id: int
    likes: List["TweetLike"]

    class Config(ConfigDict):
        from_attributes = True


class UserBase(BaseModel):
    name: str
    api_key: str


class UserCreate(UserBase):
    pass


class User(UserBase):
    id: int
    followers: Optional[List[int]] = None
    following: Optional[List[int]] = None
    likes: List["TweetLike"]

    class Config(ConfigDict):
        from_attributes = True


class LikeBase(BaseModel):
    user_id: int
    tweet_id: int


class LikeCreate(LikeBase):
    pass


class Like(LikeBase):
    id: int

    class Config(ConfigDict):
        from_attributes = True


class FollowerBase(BaseModel):
    follower_id: int
    followed_id: int


class FollowerCreate(FollowerBase):
    pass


class Follower(FollowerBase):
    id: int

    class Config(ConfigDict):
        from_attributes = True


class TweetLikeBase(BaseModel):
    user_id: int
    tweet_id: int


class TweetLikeCreate(TweetLikeBase):
    pass


class TweetLike(TweetLikeBase):
    id: int

    class Config(ConfigDict):
        from_attributes = True


class MediaBase(BaseModel):
    filename: str
    user_id: int
    tweet_id: Optional[int] = None


class MediaCreate(MediaBase):
    pass


class Media(MediaBase):
    id: int

    class Config(ConfigDict):
        from_attributes = True
