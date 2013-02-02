from sqlalchemy import Boolean, Column, Integer, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from trpycore.timezone import tz
from trsvcscore.db.models.base import Base
from trsvcscore.db.models.accounts_models import Tenant, User
from trsvcscore.db.models.common_models import Location, Organization, Technology

class JobPositionType(Base):
    __tablename__ = "job_position_type"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    description = Column(String(1024))

class JobRequisitionStatus(Base):
    __tablename__ = "job_requisition_status"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    description = Column(String(1024))

class JobRequisition(Base):
    __tablename__ = "job_requisition"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("accounts_tenant.id"))
    user_id = Column(Integer, ForeignKey("accounts_user.id"))
    position_type_id = Column(Integer, ForeignKey("job_position_type.id"))
    location_id = Column(Integer, ForeignKey("location.id"))
    status_id = Column(Integer, ForeignKey("job_requisition_status.id"))
    title = Column(String(100))
    description = Column(Text(4096))
    salary_start = Column(Integer)
    salary_end = Column(Integer)
    created = Column(DateTime, default=tz.utcnow)
    telecommute = Column(Boolean)
    relocation = Column(Boolean)
    employer_requisition_identifier = Column(String(100))

    tenant = relationship(Tenant, backref="job_requisitions")
    user = relationship(User, backref="job_requisitions")
    position_type = relationship(JobPositionType)
    location = relationship(Location)
    status = relationship(JobRequisitionStatus)
    technologies = relationship(Technology, secondary=lambda: JobRequisitionTechnology.__table__)

class JobRequisitionTechnology(Base):
    __tablename__ = "job_requisition_technology"
    __table_args__ = (UniqueConstraint('requisition_id', 'technology_id'),)

    id = Column(Integer, primary_key=True)
    requisition_id = Column(Integer, ForeignKey("job_requisition.id"))
    technology_id = Column(Integer, ForeignKey("technology.id"))
    yrs_experience = Column(Integer)

    requisition = relationship(JobRequisition, backref="requisition_technologies")
    technology = relationship(Technology)

class JobLocationPref(Base):
    __tablename__ = "job_location_pref"
    __table_args__ = (UniqueConstraint('user_id', 'location_id'),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("accounts_user.id"))
    location_id = Column(Integer, ForeignKey("location.id"))

    user = relationship(User)
    location = relationship(Location)

class JobOrganizationPref(Base):
    __tablename__ = "job_organization_pref"
    __table_args__ = (UniqueConstraint('user_id', 'organization_id'),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("accounts_user.id"))
    organization_id = Column(Integer, ForeignKey("organization.id"))

    user = relationship(User)
    organization = relationship(Organization)

class JobTechnologyPref(Base):
    __tablename__ = "job_technology_pref"
    __table_args__ = (UniqueConstraint('user_id', 'technology_id'),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("accounts_user.id"))
    technology_id = Column(Integer, ForeignKey("technology.id"))

    user = relationship(User)
    technology = relationship(Technology)

class JobPositionTypePref(Base):
    __tablename__ = "job_position_type_pref"
    __table_args__ = (UniqueConstraint('user_id', 'position_type_id'),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("accounts_user.id"))
    position_type_id = Column(Integer, ForeignKey("job_position_type.id"))
    salary_start = Column(Integer, nullable=True)
    salary_end = Column(Integer, nullable=True)

    user = relationship(User)
    position_type = relationship(JobPositionType)

class JobApplicationType(Base):
    __tablename__ = "job_application_type"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    description = Column(String(1024))

class JobApplicationStatus(Base):
    __tablename__ = "job_application_status"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    description = Column(String(1024))

class JobApplication(Base):
    __tablename__ = "job_application"
    __table_args__ = (UniqueConstraint('tenant_id', 'user_id', 'requisition_id'),)

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("accounts_tenant.id"))
    user_id = Column(Integer, ForeignKey("accounts_user.id"))
    requisition_id = Column(Integer, ForeignKey("job_requisition.id"))
    type_id = Column(Integer, ForeignKey("job_application_type.id"))
    status_id = Column(Integer, ForeignKey("job_application_status.id"))
    created = Column(DateTime, default=tz.utcnow)

    tenant = relationship(Tenant, backref="job_applications")
    user = relationship(User, backref="job_applications")
    requisition = relationship(JobRequisition, backref="job_applications")
    type = relationship(JobApplicationType)
    status = relationship(JobApplicationStatus)

class JobApplicationScore(Base):
    __tablename__ = "job_application_score"
    __table_args__ = (UniqueConstraint('tenant_id', 'user_id', 'application_id'),)

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("accounts_tenant.id"))
    user_id = Column(Integer, ForeignKey("accounts_user.id"))
    application_id = Column(Integer, ForeignKey("job_application.id"))
    technical_score = Column(Integer)
    communication_score = Column(Integer)
    cultural_fit_score = Column(Integer)

    tenant = relationship(Tenant)
    user = relationship(User)
    application = relationship(JobApplication)

class JobApplicationLog(Base):
    __tablename__ = "job_application_log"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("accounts_tenant.id"))
    user_id = Column(Integer, ForeignKey("accounts_user.id"))
    application_id = Column(Integer, ForeignKey("job_application.id"))
    note = Column(Text(4096))

    tenant = relationship(Tenant)
    user = relationship(User)
    application = relationship(JobApplication, backref="job_application_logs")

class JobApplicationVote(Base):
    __tablename__ = "job_application_vote"
    __table_args__ = (UniqueConstraint('tenant_id', 'user_id', 'application_id'),)

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("accounts_tenant.id"))
    user_id = Column(Integer, ForeignKey("accounts_user.id"))
    application_id = Column(Integer, ForeignKey("job_application.id"))
    yes = Column(Boolean, nullable=True)

    tenant = relationship(Tenant)
    user = relationship(User)
    application = relationship(JobApplication, backref="job_application_votes")

class JobInterviewOfferType(Base):
    __tablename__ = "job_interview_offer_type"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    description = Column(String(1024))

class JobInterviewOfferStatus(Base):
    __tablename__ = "job_interview_offer_status"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    description = Column(String(1024))

class JobInterviewOffer(Base):
    __tablename__ = "job_interview_offer"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("accounts_tenant.id"))
    candidate_id = Column(Integer, ForeignKey("accounts_user.id"))
    employee_id = Column(Integer, ForeignKey("accounts_user.id"))
    application_id = Column(Integer, ForeignKey("job_application.id"))
    type_id = Column(Integer, ForeignKey("job_interview_offer_type.id"))
    status_id = Column(Integer, ForeignKey("job_interview_offer_status.id"))
    created = Column(DateTime, default=tz.utcnow)
    expires = Column(DateTime)

    tenant = relationship(Tenant, backref="job_interview_offers")
    candidate = relationship(User, primaryjoin="JobInterviewOffer.candidate_id==User.id", backref="job_interview_offers")
    employee = relationship(User, primaryjoin="JobInterviewOffer.employee_id==User.id")
    application = relationship(JobApplication)
    type = relationship(JobInterviewOfferType)
    status = relationship(JobInterviewOfferStatus)

class JobOfferStatus(Base):
    __tablename__ = "job_offer_status"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    description = Column(String(1024))

class JobOffer(Base):
    __tablename__ = "job_offer"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("accounts_tenant.id"))
    employee_id = Column(Integer, ForeignKey("accounts_user.id"))
    candidate_id = Column(Integer, ForeignKey("accounts_user.id"))
    application_id = Column(Integer, ForeignKey("job_application.id"))
    status_id = Column(Integer, ForeignKey("job_offer_status.id"))
    salary = Column(Integer)
    created = Column(DateTime, default=tz.utcnow)

    tenant = relationship(Tenant, backref="job_offers")
    employee = relationship(User, primaryjoin="JobOffer.employee_id==User.id", backref="job_offers")
    candidate = relationship(User, primaryjoin="JobOffer.candidate_id==User.id")
    application = relationship(JobApplication)
    status = relationship(JobOfferStatus)

class JobNote(Base):
    __tablename__ = "job_note"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("accounts_tenant.id"))
    employee_id = Column(Integer, ForeignKey("accounts_user.id"))
    candidate_id = Column(Integer, ForeignKey("accounts_user.id"))
    note = Column(Text(4096))

    tenant = relationship(Tenant)
    employee = relationship(User, primaryjoin="JobNote.employee_id==User.id")
    candidate = relationship(User, primaryjoin="JobNote.candidate_id==User.id")

class JobEvent(Base):
    __tablename__ = "job_event"

    id = Column(Integer, primary_key=True)
    title = Column(String(255))
    start = Column(DateTime)
    end = Column(DateTime)
    description = Column(Text(4096))

    candidates = relationship(User, secondary=lambda: JobEventCandidate.__table__)

class JobEventCandidate(Base):
    __tablename__ = "job_event_candidate"
    __table_args__ = (UniqueConstraint('event_id', 'user_id'),)

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("job_event.id"))
    user_id = Column(Integer, ForeignKey("accounts_user.id"))

    event = relationship(JobEvent)
    user = relationship(User)
