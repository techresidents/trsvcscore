from sqlalchemy import Boolean, Column, Integer, Date, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from trsvcscore.db.models.base import Base
from trsvcscore.db.models.django_models import User
from trsvcscore.db.models.common_models import ExpertiseType, Technology

class AccountCodeType(Base):
    __tablename__ = "accounts_codetype"

    id = Column(Integer, primary_key=True)
    type = Column(String(100))
    description = Column(String(1024))

class AccountCode(Base):
    __tablename__ = "accounts_code"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("auth_user.id"))
    type_id = Column(Integer, ForeignKey("accounts_codetype.id"))
    code = Column(String(255))
    created = Column(DateTime, server_default=func.current_timestamp())
    used = Column(DateTime, nullable=True)

    user = relationship(User)
    type = relationship(AccountCodeType)

class AccountRequest(Base):
    __tablename__ = "accounts_request"

    id = Column(Integer, primary_key=True)
    first_name = Column(String(30))
    last_name = Column(String(30))
    email = Column(String(75), unique=True)
    code = Column(String(255))
    created = Column(DateTime, server_default=func.current_timestamp())

class Skill(Base):
    __tablename__ = "accounts_skill"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("auth_user.id"))
    technology_id = Column(Integer, ForeignKey("technology.id"))
    expertise_type_id = Column(Integer, ForeignKey("expertise_type.id"))
    yrs_experience = Column(Integer)

    user = relationship(User)
    technology = relationship(Technology)
    expertise_type = relationship(ExpertiseType)

class UserProfile(Base):
    __tablename__ = "accounts_userprofile"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("auth_user.id"))
    developer_since = Column(Date, nullable=True)
    email_upcoming_chats = Column(Boolean)
    email_new_chat_topics = Column(Boolean)
    timezone = Column(String(255))

    user = relationship(User)
