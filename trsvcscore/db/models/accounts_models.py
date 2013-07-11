from sqlalchemy import Boolean, Column, Integer, Date, DateTime, ForeignKey, String
from sqlalchemy.orm import backref, relationship
from sqlalchemy.sql import func

from trsvcscore.db.models.base import Base

class Tenant(Base):
    __tablename__ = "accounts_tenant"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    domain = Column(String(255))

class User(Base):
    __tablename__ = "accounts_user"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("accounts_tenant.id"))
    username = Column(String(254))
    first_name = Column(String(30))
    last_name = Column(String(30))
    email = Column(String(254))
    password = Column(String(128))
    timezone = Column(String(255))
    is_staff = Column(Boolean)
    is_active = Column(Boolean)
    last_login = Column(DateTime)
    date_joined = Column(DateTime)
    otp_enabled = Column(Boolean, default=False)

    tenant = relationship(Tenant)

class AccountCodeType(Base):
    __tablename__ = "accounts_codetype"

    id = Column(Integer, primary_key=True)
    type = Column(String(100))
    description = Column(String(1024))

class AccountCode(Base):
    __tablename__ = "accounts_code"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("accounts_user.id"))
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

class DeveloperProfile(Base):
    __tablename__ = "accounts_developer_profile"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("accounts_user.id"))
    location = Column(String(100), nullable=True)
    developer_since = Column(Date, nullable=True)
    email_upcoming_chats = Column(Boolean, default=False)
    email_new_chat_topics = Column(Boolean, default=False)
    email_new_job_opps = Column(Boolean, default=True)
    actively_seeking = Column(Boolean, default=False)

    user = relationship(User, backref=backref("developer_profile", uselist=False))

class EmployerProfile(Base):
    __tablename__ = "accounts_employer_profile"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("accounts_user.id"))

    user = relationship(User)

class OneTimePasswordType(Base):
    __tablename__ = "accounts_one_time_password_type"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True)
    description = Column(String(1024))

class OneTimePassword(Base):
    __tablename__ = "accounts_one_time_password"

    id = Column(Integer, primary_key=True)
    type_id = Column(Integer, ForeignKey("accounts_one_time_password_type.id"))
    user_id = Column(Integer, ForeignKey("accounts_user.id"))
    secret = Column(String(1024))
    
    type = relationship(OneTimePasswordType)
    user = relationship(User)
