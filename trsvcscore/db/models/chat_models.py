from sqlalchemy import Boolean, Column, Float, Integer, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from trsvcscore.db.models.base import Base
from trsvcscore.db.models.django_models import User
from trsvcscore.db.models.common_models import Tag, Topic, Quality

class ChatType(Base):
    __tablename__ = "chat_type"

    id = Column(Integer, primary_key=True, unique=True)
    name = Column(String(100))
    description = Column(String(1024))

class ChatMessageType(Base):
    __tablename__ = "chat_message_type"

    id = Column(Integer, primary_key=True, unique=True)
    name = Column(String(100))
    description = Column(String(1024))

class ChatMessageFormatType(Base):
    __tablename__ = "chat_message_format_type"

    id = Column(Integer, primary_key=True, unique=True)
    name = Column(String(100))
    description = Column(String(1024))

class Chat(Base):
    __tablename__ = "chat"

    id = Column(Integer, primary_key=True)
    type_id = Column(Integer, ForeignKey("chat_type.id"))
    topic_id = Column(Integer, ForeignKey("topic.id"))
    start = Column(DateTime)
    end = Column(DateTime)
    registration_start = Column(DateTime, nullable=True)
    registration_end = Column(DateTime, nullable=True)
    checkin_start = Column(DateTime, nullable=True)
    checkin_end = Column(DateTime, nullable=True)

    type = relationship(ChatType)
    topic = relationship(Topic, backref="chats")

class ChatSession(Base):
    __tablename__ = "chat_session"

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("chat.id"))
    token = Column(String(1024), nullable=True, unique=True)
    participants = Column(Integer, default=0)
    start = Column(DateTime, nullable=True)
    end = Column(DateTime, nullable=True)

    chat = relationship(Chat, backref="chat_sessions")
    users = relationship(User, secondary=lambda: ChatUser.__table__)

class ChatUser(Base):
    __tablename__ = "chat_user"

    id = Column(Integer, primary_key=True)
    chat_session_id = Column(Integer, ForeignKey("chat_session.id"))
    user_id = Column(Integer, ForeignKey("auth_user.id"))
    token = Column(String(1024), nullable=True)
    participant = Column(Integer)

    chat_session = relationship(ChatSession, backref="chat_users")
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
    topic_id = Column(Integer, ForeignKey("topic.id"))
    start = Column(DateTime)
    end = Column(DateTime, nullable=True)

    chat_session = relationship(ChatSession, backref="chat_minutes")
    topic = relationship(Topic, backref="chat_minutes")

class ChatRegistration(Base):
    __tablename__ = "chat_registration"

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("chat.id"))
    user_id = Column(Integer, ForeignKey("auth_user.id"))
    chat_session_id = Column(Integer, ForeignKey("chat_session.id"), nullable=True)
    checked_in = Column(Boolean, default=False)

    chat = relationship(Chat, backref="chat_registrations")
    user = relationship(User)
    chat_session = relationship(ChatSession, backref="chat_registrations")

class ChatScheduleJob(Base):
    __tablename__ = "chat_schedule_job"

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("chat.id"), unique=True)
    start = Column(DateTime, server_default=func.current_timestamp())
    end = Column(DateTime, nullable=True)

    chat = relationship(Chat)

class ChatPersistJob(Base):
    __tablename__ = "chat_persist_job"

    id = Column(Integer, primary_key=True)
    chat_session_id = Column(Integer, ForeignKey("chat_session.id"))
    created = Column(DateTime, server_default=func.current_timestamp())
    start = Column(DateTime, nullable=True)
    end = Column(DateTime, nullable=True)
    owner = Column(String(1024), nullable=True)

    chat_session = relationship(ChatSession)

class ChatTag(Base):
    __tablename__ = "chat_tag"
    __table_args__ = (UniqueConstraint('user_id', 'chat_minute_id', 'name'),
        )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("auth_user.id"))
    chat_minute_id = Column(Integer, ForeignKey("chat_minute.id"))
    tag_id = Column(Integer, ForeignKey("tag.id"), nullable=True)
    name = Column(String(1024))
    deleted = Column(Boolean, default=False)

    user = relationship(User)
    chat_minute = relationship(ChatMinute, backref="chat_tags")
    tag = relationship(Tag)

class ChatSpeakingMarker(Base):
    __tablename__ = "chat_speaking_marker"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("auth_user.id"))
    chat_minute_id = Column(Integer, ForeignKey("chat_minute.id"))
    start = Column(DateTime)
    end = Column(DateTime)

    user = relationship(User)
    chat_minute = relationship(ChatMinute, backref="chat_speaking_markers")

class ChatMessage(Base):
    __tablename__ = "chat_message"

    id = Column(Integer, primary_key=True)
    message_id = Column(String(1024), unique=True)
    chat_session_id = Column(Integer, ForeignKey("chat_session.id"))
    type_id = Column(Integer, ForeignKey("chat_message_type.id"))
    format_type_id = Column(Integer, ForeignKey("chat_message_format_type.id"))
    timestamp = Column(Float)
    time = Column(DateTime)
    data = Column(Text)

    chat_session = relationship(ChatSession)
    type = relationship(ChatMessageType)
    format_type = relationship(ChatMessageFormatType)
