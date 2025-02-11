from sqlalchemy import Column, Integer, String, ARRAY, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Модель User
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    api_key = Column(String, unique=True, index=True)
    followers = relationship("Follower", foreign_keys="[Follower.followed_id]", back_populates="followed")
    following = relationship("Follower", foreign_keys="[Follower.follower_id]", back_populates="follower")
    likes = relationship("Like", back_populates="user")  # Обратное отношение к Like
    media = relationship("Media", back_populates="user")
    tweets = relationship("Tweet", back_populates="author")

# Модель Tweet
class Tweet(Base):
    __tablename__ = "tweets"

    id = Column(Integer, primary_key=True, index=True)
    tweet_data = Column(String, index=True)
    tweet_media_ids = Column(ARRAY(Integer), nullable=True)
    author_id = Column(Integer, ForeignKey('users.id'))  # Внешний ключ для связи с таблицей users
    likes = relationship("Like", back_populates="tweet")  # Обратное отношение к Like
    media_items = relationship("Media", back_populates="tweet")
    author = relationship("User", back_populates="tweets")  # Определение отношения к модели User

# Модель Like
class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    tweet_id = Column(Integer, ForeignKey('tweets.id'), nullable=False)

    # Определение отношений
    user = relationship("User", back_populates="likes")
    tweet = relationship("Tweet", back_populates="likes")

# Модель Media
class Media(Base):
    __tablename__ = "media"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tweet_id = Column(Integer, ForeignKey("tweets.id"), nullable=True)

    user = relationship("User", back_populates="media")
    tweet = relationship("Tweet", back_populates="media_items")

# Модель Follower
class Follower(Base):
    __tablename__ = "followers"
    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    followed_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    follower = relationship("User", foreign_keys=[follower_id], back_populates="following")
    followed = relationship("User", foreign_keys=[followed_id], back_populates="followers")
