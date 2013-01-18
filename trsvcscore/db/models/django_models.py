from sqlalchemy import Boolean, Column, Integer, DateTime, String

from trsvcscore.db.models.base import Base

class AuthUser(Base):
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
