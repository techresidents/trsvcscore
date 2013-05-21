from sqlalchemy import Boolean, Column, Integer, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from trpycore.timezone import tz
from trsvcscore.db.models.base import Base
from trsvcscore.db.models.accounts_models import User
from trsvcscore.db.models.common_models import MimeType, Topic

class Chat(Base):
    __tablename__ = "chat"

    id = Column(Integer, primary_key=True)
    topic_id = Column(Integer, ForeignKey("topic.id"))
    token = Column(String(1024), nullable=True, unique=True)
    start = Column(DateTime, nullable=True)
    end = Column(DateTime, nullable=True)
    max_participants = Column(Integer, default=1)
    no_participants = Column(Integer, default=0)
    record = Column(Boolean, default=False)

    topic = relationship(Topic, backref="chats")
    users = relationship(User, secondary=lambda: ChatParticipant.__table__)

class ChatParticipant(Base):
    __tablename__ = "chat_participant"
    __table_args__ = (UniqueConstraint('chat_id', 'user_id'),
        )

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("chat.id"))
    user_id = Column(Integer, ForeignKey("accounts_user.id"))
    participant = Column(Integer)

    chat = relationship(Chat, backref="chat_participants")
    user = relationship(User)

class ChatArchive(Base):
    __tablename__ = "chat_archive"

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("chat.id"))
    mime_type_id = Column(Integer, ForeignKey("mime_type.id"))
    path = Column(String(1024))
    public = Column(Boolean, default=False)
    waveform = Column(Text)
    waveform_path = Column(String(1024))
    length = Column(Integer, nullable=True)
    offset = Column(Integer, nullable=True)

    chat = relationship(Chat, backref="chat_archives")
    mime_type = relationship(MimeType)

class ChatPersistJob(Base):
    __tablename__ = "chat_persist_job"

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("chat.id"))
    created = Column(DateTime, default=tz.utcnow)
    start = Column(DateTime, nullable=True)
    end = Column(DateTime, nullable=True)
    owner = Column(String(1024), nullable=True)
    successful = Column(Boolean, nullable=True)

    chat = relationship(Chat)

class ChatArchiveJob(Base):
    __tablename__ = "chat_archive_job"

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("chat.id"))
    created = Column(DateTime, default=tz.utcnow)
    not_before = Column(DateTime, default=tz.utcnow)
    start = Column(DateTime, nullable=True)
    end = Column(DateTime, nullable=True)
    owner = Column(String(1024), nullable=True)
    successful = Column(Boolean, nullable=True)
    retries_remaining = Column(Integer)

    chat = relationship(Chat)

class ChatReel(Base):
    __tablename__ = "chat_reel"
    __table_args__ = (UniqueConstraint('chat_id', 'user_id'),
        )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("accounts_user.id"))
    chat_id = Column(Integer, ForeignKey("chat.id"))
    rank = Column(Integer)

    user = relationship(User, backref="chat_reels")
    chat = relationship(Chat)
