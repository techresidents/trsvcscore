from sqlalchemy import Boolean, Column, Float, Integer, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from trsvcscore.db.models.base import Base
from trsvcscore.db.models.accounts_models import User
from trsvcscore.db.models.common_models import MimeType, Tag, Topic, Quality

class ChatType(Base):
    __tablename__ = "chat_type"

    id = Column(Integer, primary_key=True, unique=True)
    name = Column(String(100), unique=True)
    description = Column(String(1024))

class ChatMessageType(Base):
    __tablename__ = "chat_message_type"

    id = Column(Integer, primary_key=True, unique=True)
    name = Column(String(100), unique=True)
    description = Column(String(1024))

class ChatMessageFormatType(Base):
    __tablename__ = "chat_message_format_type"

    id = Column(Integer, primary_key=True, unique=True)
    name = Column(String(100), unique=True)
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
    record = Column(Boolean, default=False)

    type = relationship(ChatType)
    topic = relationship(Topic, backref="chats")

class ChatSession(Base):
    __tablename__ = "chat_session"

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("chat.id"))
    token = Column(String(1024), nullable=True, unique=True)
    participants = Column(Integer, default=0)
    connect = Column(DateTime, nullable=True)
    publish = Column(DateTime, nullable=True)
    start = Column(DateTime, nullable=True)
    end = Column(DateTime, nullable=True)

    chat = relationship(Chat, backref="chat_sessions")
    users = relationship(User, secondary=lambda: ChatUser.__table__)

class ChatUser(Base):
    __tablename__ = "chat_user"
    __table_args__ = (UniqueConstraint('chat_session_id', 'user_id'),
        )

    id = Column(Integer, primary_key=True)
    chat_session_id = Column(Integer, ForeignKey("chat_session.id"))
    user_id = Column(Integer, ForeignKey("accounts_user.id"))
    token = Column(String(1024), nullable=True)
    participant = Column(Integer)

    chat_session = relationship(ChatSession, backref="chat_users")
    user = relationship(User)

class ChatArchiveType(Base):
    __tablename__ = "chat_archive_type"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True)
    description = Column(String(1024))

class ChatArchive(Base):
    __tablename__ = "chat_archive"

    id = Column(Integer, primary_key=True)
    type_id = Column(Integer, ForeignKey("chat_archive_type.id"))
    chat_session_id = Column(Integer, ForeignKey("chat_session.id"))
    mime_type_id = Column(Integer, ForeignKey("mime_type.id"))
    path = Column(String(1024))
    public = Column(Boolean, default=False)
    waveform = Column(Text)
    waveform_path = Column(String(1024))
    length = Column(Integer, nullable=True)
    offset = Column(Integer, nullable=True)

    type = relationship(ChatArchiveType)
    chat_session = relationship(ChatSession, backref="chat_archives")
    mime_type = relationship(MimeType)
    users = relationship(User, secondary=lambda: ChatArchiveUser.__table__)

class ChatArchiveUser(Base):
    __tablename__ = "chat_archive_user"

    id = Column(Integer, primary_key=True)
    chat_archive_id = Column(Integer, ForeignKey("chat_archive.id"))
    user_id = Column(Integer, ForeignKey("accounts_user.id"))

    chat_archive = relationship(ChatArchive)
    user = relationship(User)

class ChatFeedback(Base):
    __tablename__ = "chat_feedback"

    id = Column(Integer, primary_key=True)
    chat_session_id = Column(Integer, ForeignKey("chat_session.id"))
    user_id = Column(Integer, ForeignKey("accounts_user.id"))
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
    user_id = Column(Integer, ForeignKey("accounts_user.id"))
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
    successful = Column(Boolean, nullable=True)

    chat_session = relationship(ChatSession)

class ChatArchiveJob(Base):
    __tablename__ = "chat_archive_job"

    id = Column(Integer, primary_key=True)
    chat_session_id = Column(Integer, ForeignKey("chat_session.id"))
    created = Column(DateTime, server_default=func.current_timestamp())
    not_before = Column(DateTime, server_default=func.current_timestamp())
    start = Column(DateTime, nullable=True)
    end = Column(DateTime, nullable=True)
    owner = Column(String(1024), nullable=True)
    successful = Column(Boolean, nullable=True)
    retries_remaining = Column(Integer)

    chat_session = relationship(ChatSession)

class ChatTag(Base):
    __tablename__ = "chat_tag"
    __table_args__ = (UniqueConstraint('user_id', 'chat_minute_id', 'name'),
        )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("accounts_user.id"))
    chat_minute_id = Column(Integer, ForeignKey("chat_minute.id"))
    tag_id = Column(Integer, ForeignKey("tag.id"), nullable=True)
    time = Column(DateTime)
    name = Column(String(1024))
    deleted = Column(Boolean, default=False)

    user = relationship(User)
    chat_minute = relationship(ChatMinute, backref="chat_tags")
    tag = relationship(Tag)

class ChatSpeakingMarker(Base):
    __tablename__ = "chat_speaking_marker"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("accounts_user.id"))
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

class ChatHighlightSession(Base):
    __tablename__ = "chat_highlight_session"
    __table_args__ = (UniqueConstraint('chat_session_id', 'user_id'),
        )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("accounts_user.id"))
    chat_session_id = Column(Integer, ForeignKey("chat_session.id"))
    rank = Column(Integer)

    user = relationship(User, backref="chat_highlight_sessions")
    chat_session = relationship(ChatSession)
