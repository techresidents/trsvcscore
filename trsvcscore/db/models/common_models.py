from sqlalchemy import Boolean, Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship, backref

from trsvcscore.db.models.base import Base
from trsvcscore.db.models.accounts_models import User

class Concept(Base):
    __tablename__ = "concept"

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey("concept.id"))
    name = Column(String(100), unique=True)
    description = Column(String(1024))

    children = relationship("Concept", backref=backref("parent", remote_side=[id]))

class ExpertiseType(Base):
    __tablename__ = "expertise_type"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True)
    value = Column(Integer)
    description = Column(String(1024))

class MimeType(Base):
    __tablename__ = "mime_type"

    id = Column(Integer, primary_key=True)
    extension = Column(String(16))
    type = Column(String(255))

class Location(Base):
    __tablename__ = "location"

    id = Column(Integer, primary_key=True)
    region = Column(String(100))
    country = Column(String(100))
    state = Column(String(100))
    city = Column(String(100))
    zip = Column(String(25))
    county = Column(String(100))

class Organization(Base):
    __tablename__ = "organization"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True)
    description = Column(String(1024))


class Tag(Base):
    __tablename__ = "tag"

    id = Column(Integer, primary_key=True, unique=True)
    name = Column(String(100), unique=True)
    concept_id = Column(Integer, ForeignKey("concept.id"))

    concept = relationship(Concept)

class TechnologyType(Base):
    __tablename__ = "technology_type"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True)
    description = Column(String(1024))

class Technology(Base):
    __tablename__ = "technology"

    id = Column(Integer, primary_key=True)
    type_id = Column(Integer, ForeignKey("technology_type.id"))
    name = Column(String(100), unique=True)
    description = Column(String(1024))

    type = relationship(TechnologyType)

class Quality(Base):
    __tablename__ = "quality"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True)
    description = Column(String(1024))

class TopicType(Base):
    __tablename__ = "topic_type"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True)
    description = Column(String(1024))

class Topic(Base):
    __tablename__ = "topic"

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey("topic.id"))
    rank = Column(Integer) 
    type_id = Column(Integer, ForeignKey("topic_type.id"))
    title = Column(String(100))
    description = Column(String(2048))
    duration = Column(Integer)
    recommended_participants = Column(Integer)
    public = Column(Boolean, default=True)
    active = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey("accounts_user.id"))

    children = relationship("Topic", backref=backref("parent", remote_side=[id]))
    type = relationship(TopicType)
    user = relationship(User)

class Document(Base):
    __tablename__ = "document"

    id = Column(Integer, primary_key=True)
    name = Column(String(1024))
    path = Column(String(1024))
    mime_type_id = Column(Integer, ForeignKey("mime_type.id"))

    mime_type = relationship(MimeType)

class Skill(Base):
    __tablename__ = "skill"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("accounts_user.id"))
    technology_id = Column(Integer, ForeignKey("technology.id"))
    expertise_type_id = Column(Integer, ForeignKey("expertise_type.id"))
    yrs_experience = Column(Integer)

    user = relationship(User, backref="skills")
    technology = relationship(Technology)
    expertise_type = relationship(ExpertiseType)

class TalkingPoint(Base):
    __tablename__ = "talking_point"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("accounts_user.id"))
    topic_id = Column(Integer, ForeignKey("topic.id"))
    rank = Column(Integer)
    point = Column(String(4096))

    user = relationship(User)
    topic = relationship(Topic, backref="talking_points")
