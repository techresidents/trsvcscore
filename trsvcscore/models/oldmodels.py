from sqlalchemy import Boolean, Column, Integer, DateTime, ForeignKey, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = "auth_user"

    id = Column(Integer, primary_key=True)
    username = Column(String(75))
    first_name = Column(String(30))
    last_name = Column(String(30))
    email = Column(String(75))
    password = Column(String(128))
    is_staff = Column(Boolean)
    is_active = Column(Boolean)
    last_login = Column(DateTime)
    date_joined = Column(DateTime)

class TopicType(Base):
    __tablename__ = "topic_type"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    description = Column(String(1024))

class Topic(Base):
    __tablename__ = "topic"

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey("topic.id"))
    rank = Column(Integer) 
    type_id = Column(Integer, ForeignKey("topic_type.id"))
    type = relationship("TopicType")
    title = Column(String(100))
    description = Column(String(2048))
    duration = Column(Integer)
    public = Column(Boolean)
    user_id = Column(Integer, ForeignKey("auth_user.id"))
    user = relationship("User")

class Quality(Base):
    __tablename__ = "quality"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    description = Column(String(1024))

class ChatType(Base):
    __tablename__ = "chat_type"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    description = Column(String(1024))

class Chat(Base):
    __tablename__ = "chat"

    id = Column(Integer, primary_key=True)
    type_id = Column(Integer, ForeignKey("chat_type.id"))
    type = relationship("ChatType")
    topic_id = Column(Integer, ForeignKey("topic.id"))
    topic = relationship("Topic")
    start = Column(DateTime)
    end = Column(DateTime)

class ChatSession(Base):
    __tablename__ = "chat_session"

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("chat.id"))
    token = Column(String(1024))
    participants = Column(Integer)

    chat = relationship("Chat", backref="chat_sessions")
    users = relationship("User", secondary=lambda: ChatUser.__table__)


class ChatUser(Base):
    __tablename__ = "chat_user"

    id = Column(Integer, primary_key=True)
    chat_session_id = Column(Integer, ForeignKey("chat_session.id"))
    chat_session = relationship("ChatSession")
    user_id = Column(Integer, ForeignKey("auth_user.id"))
    user = relationship("User")
    token = Column(String(1024))
    participant = Column(Integer)

class ChatFeedback(Base):
    __tablename__ = "chat_feedback"

    id = Column(Integer, primary_key=True)
    chat_session_id = Column(Integer, ForeignKey("chat_session.id"))
    user_id = Column(Integer, ForeignKey("auth_user.id"))
    overall_quality_id = Column(Integer, ForeignKey("quality.id"))
    technical_quality_id = Column(Integer, ForeignKey("quality.id"))

    chat_session = relationship(ChatSession, backref="chat_feedbacks")
    user = relationship(User)
    overall_quality = relationship(Quality, primaryjoin=Quality.id == overall_quality_id)
    technical_quality = relationship(Quality, primaryjoin=Quality.id == technical_quality_id)

class ChatMinute(Base):
    __tablename__ = "chat_minute"

    id = Column(Integer, primary_key=True)
    chat_session_id = Column(Integer, ForeignKey("chat_session.id"))

    chat_session = relationship(ChatSession, backref="chat_minutes")

class ChatRegistration(Base):
    __tablename__ = "chat_registration"

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("chat.id"))
    user_id = Column(Integer, ForeignKey("auth_user.id"))
    chat_session_id = Column(Integer, ForeignKey("chat_session.id"), nullable=True)
    checked_in = Column(Boolean)

    chat = relationship(Chat, backref="chat_registrations")
    user = relationship(User)
    chat_session = relationship(ChatSession, backref="chat_registrations")

class ChatScheduleJob(Base):
    __tablename__ = "chat_schedule_job"

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("chat.id"))
    chat = relationship("Chat")
    start = Column(DateTime, server_default=func.current_timestamp())
    end = Column(DateTime, nullable=True)

