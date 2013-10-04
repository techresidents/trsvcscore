from sqlalchemy import Boolean, Column, Integer, Date, DateTime, ForeignKey, String
from sqlalchemy.orm import backref, relationship

from trsvcscore.db.models.base import Base
from trsvcscore.db.models.accounts_models import Tenant


class CompanySize(Base):
    __tablename__ = "company_size"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    description = Column(String(1024))

class CompanyProfile(Base):
    __tablename__ = "company_profile"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("accounts_tenant.id"))
    size_id = Column(Integer, ForeignKey("company_size.id"), default=1)
    name = Column(String(100), nullable=True)
    description = Column(String(4096), nullable=True)
    location = Column(String(255), nullable=True)
    url = Column(String(255), nullable=True)

    tenant = relationship(Tenant, backref=backref("company_profile", uselist=False))
    size = relationship(CompanySize)