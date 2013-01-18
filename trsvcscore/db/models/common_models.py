from sqlalchemy import Boolean, Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship, backref

from trsvcscore.db.models.base import Base
from trsvcscore.db.models.accounts_models import User

RESOURCE_TYPES = {
    "DOCUMENT": 1,
    "WHITEBOARD": 2,
    "CODEBOARD": 3,
}

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

class Quality(Base):
    __tablename__ = "quality"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True)
    description = Column(String(1024))

class ResourceType(Base):
    __tablename__ = "resource_type"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True)
    description = Column(String(1024))

class Resource(Base):
    __tablename__ = "resource"

    id = Column(Integer, primary_key=True)
    type_id = Column(Integer, ForeignKey("resource_type.id"))
    __mapper_args__ = { "polymorphic_on": type_id }

    type = relationship(ResourceType)


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
    resources = relationship(Resource, secondary=lambda: TopicResource.__table__)

class TopicResource(Base):
    __tablename__ = "topic_resources"

    id = Column(Integer, primary_key=True)
    topic_id = Column(Integer, ForeignKey("topic.id"))
    resource_id = Column(Integer, ForeignKey("resource.id"))

    topic = relationship(Topic)
    resource = relationship(Resource)

class Document(Base):
    __tablename__ = "document"

    id = Column(Integer, primary_key=True)
    name = Column(String(1024))
    path = Column(String(1024))
    mime_type_id = Column(Integer, ForeignKey("mime_type.id"))

    mime_type = relationship(MimeType)

class DocumentResource(Resource):
    __tablename__ = "document_resource"
    __mapper_args__ = { "polymorphic_identity": RESOURCE_TYPES["DOCUMENT"]}

    resource_id = Column(Integer, ForeignKey("resource.id"), primary_key=True)
    document_id = Column(Integer, ForeignKey("document.id"))

    document = relationship(Document)

class Whiteboard(Base):
    __tablename__ = "whiteboard"

    id = Column(Integer, primary_key=True)
    name = Column(String(1024))

class WhiteboardResource(Resource):
    __tablename__ = "whiteboard_resource"
    __mapper_args__ = { "polymorphic_identity": RESOURCE_TYPES["WHITEBOARD"]}

    resource_id = Column(Integer, ForeignKey("resource.id"), primary_key=True)
    whiteboard_id = Column(Integer, ForeignKey("whiteboard.id"))

    whiteboard = relationship(Whiteboard)

class Codeboard(Base):
    __tablename__ = "codeboard"

    id = Column(Integer, primary_key=True)
    name = Column(String(1024))

class CodeboardResource(Resource):
    __tablename__ = "codeboard_resource"
    __mapper_args__ = { "polymorphic_identity": RESOURCE_TYPES["CODEBOARD"]}

    resource_id = Column(Integer, ForeignKey("resource.id"), primary_key=True)
    codeboard_id = Column(Integer, ForeignKey("codeboard.id"))

    codeboard = relationship(Codeboard)

class Skill(Base):
    __tablename__ = "skill"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("accounts_user.id"))
    technology_id = Column(Integer, ForeignKey("technology.id"))
    expertise_type_id = Column(Integer, ForeignKey("expertise_type.id"))
    yrs_experience = Column(Integer)

    user = relationship(User)
    technology = relationship(Technology)
    expertise_type = relationship(ExpertiseType)
