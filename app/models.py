from sqlalchemy import Column, Integer, String, ARRAY, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Tweet(Base):
    __tablename__ = "tweets"
    id = Column(Integer, primary_key=True, index=True)
    tweet_data = Column(String, index=True)
    tweet_media_ids = Column(ARRAY(Integer), nullable=True)
    likes = relationship("TweetLike", back_populates="tweet")
    media_items = relationship("Media", back_populates="tweet")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    api_key = Column(String, unique=True, index=True)
    followers = relationship("Follower", foreign_keys="[Follower.followed_id]", back_populates="followed")
    following = relationship("Follower", foreign_keys="[Follower.follower_id]", back_populates="follower")
    likes = relationship("TweetLike", back_populates="user")
    media = relationship("Media", back_populates="user")


class TweetLike(Base):
    __tablename__ = "tweet_likes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tweet_id = Column(Integer, ForeignKey("tweets.id"), nullable=False)

    user = relationship("User", back_populates="likes")
    tweet = relationship("Tweet", back_populates="likes")


class Media(Base):
    __tablename__ = "media"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tweet_id = Column(Integer, ForeignKey("tweets.id"), nullable=True)

    user = relationship("User", back_populates="media")
    tweet = relationship("Tweet", back_populates="media_items")


class Follower(Base):
    __tablename__ = "followers"
    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    followed_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    follower = relationship("User", foreign_keys=[follower_id], back_populates="following")
    followed = relationship("User", foreign_keys=[followed_id], back_populates="followers")
