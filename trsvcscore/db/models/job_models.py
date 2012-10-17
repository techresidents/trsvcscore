from sqlalchemy import Boolean, Column, Integer, Date, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from trsvcscore.db.models.base import Base
from trsvcscore.db.models.django_models import User
from trsvcscore.db.models.common_models import Location, Organization, Technology

class JobPreferences(Base):
    __tablename__ = "job_prefs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("auth_user.id"))

class JobPositionType(Base):
    __tablename__ = "job_positiontype"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    description = Column(String(1024))

class JobPositionTypePreference(Base):
    __tablename__ = "job_positiontypepref"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("auth_user.id"))
    position_type_id = Column(Integer, ForeignKey("job_positiontype.id"))

    user = relationship(User)
    position_type = relationship(JobPositionType)

class JobLocationPreference(Base):
    __tablename__ = "job_locationpref"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("auth_user.id"))
    location_id = Column(Integer, ForeignKey("location.id"))

    user = relationship(User)
    location = relationship(Location)

class JobOrganizationPreference(Base):
    __tablename__ = "job_organizationpref"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("auth_user.id"))
    organization_id = Column(Integer, ForeignKey("organization.id"))

    user = relationship(User)
    organization = relationship(Organization)

class JobTechnologyPreference(Base):
    __tablename__ = "job_technologypref"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("auth_user.id"))
    technology_id = Column(Integer, ForeignKey("technology.id"))

    user = relationship(User)
    technology = relationship(Technology)

class JobRequisition(Base):
    __tablename__ = "job_requisition"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    description = Column(String(1024))
    type_id = Column(Integer, ForeignKey("job_positiontype.id"))
    salary_start = Column(Integer)
    salary_end = Column(Integer)
    date_posted = Column(Date)
    is_active = Column(Boolean)

    type = relationship(JobPositionType)
    locations = relationship(Location, secondary=lambda: JobRequisitionLocation.__table__)
    technologies = relationship(Technology, secondary=lambda: JobRequisitionTechnology.__table__)

class JobRequisitionLocation(Base):
    __tablename__ = "job_requisition_locations"

    id = Column(Integer, primary_key=True)
    requisition_id = Column(Integer, ForeignKey("job_requisition.id"))
    location_id = Column(Integer, ForeignKey("location.id"))

    requisition = relationship(JobRequisition)
    location = relationship(Location)

class JobRequisitionTechnology(Base):
    __tablename__ = "job_requisition_technologies"

    id = Column(Integer, primary_key=True)
    requisition_id = Column(Integer, ForeignKey("job_requisition.id"))
    technology_id = Column(Integer, ForeignKey("technology.id"))

    requisition = relationship(JobRequisition)
    technology = relationship(Technology)

