from sqlalchemy import Boolean, Column, Integer, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from trsvcscore.models.base import Base
from trsvcscore.models.django_models import User
from trsvcscore.models.common_models import Tag, Topic, Quality

class ChatType(Base):
    __tablename__ = "chat_type"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    description = Column(String(1024))

class Chat(Base):
    __tablename__ = "chat"

    id = Column(Integer, primary_key=True)
    type_id = Column(Integer, ForeignKey("chat_type.id"))
    topic_id = Column(Integer, ForeignKey("topic.id"))
    start = Column(DateTime)
    end = Column(DateTime)
    registration_start = Column(DateTime)
    registration_end = Column(DateTime)
    checkin_start = Column(DateTime)
    checkin_end = Column(DateTime)

    type = relationship(ChatType)
    topic = relationship(Topic)

class ChatSession(Base):
    __tablename__ = "chat_session"

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("chat.id"))
    token = Column(String(1024))
    participants = Column(Integer)

    chat = relationship(Chat, backref="chat_sessions")
    users = relationship(User, secondary=lambda: ChatUser.__table__)


class ChatUser(Base):
    __tablename__ = "chat_user"

    id = Column(Integer, primary_key=True)
    chat_session_id = Column(Integer, ForeignKey("chat_session.id"))
    user_id = Column(Integer, ForeignKey("auth_user.id"))
    token = Column(String(1024))
    participant = Column(Integer)

    chat_session = relationship(ChatSession)
    user = relationship(User)

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
    chat = relationship(Chat)
    start = Column(DateTime, server_default=func.current_timestamp())
    end = Column(DateTime, nullable=True)

class ChatTag(Base):
    __tablename__ = "chat_tag"

    id = Column(Integer, primary_key=True)
    chat_minute_id = Column(Integer, ForeignKey("chat_minute.id"))
    tag_id = Column(Integer, ForeignKey("tag.id"), nullable=True)
    name = Column(String(1024))

    chat_minute = relationship(ChatMinute)
    tag = relationship(Tag)

