from sqlalchemy import Boolean, Column, Integer, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from trsvcscore.db.models.base import Base


class IndexJob(Base):
    """IndexJob data model.

    Represents a job for the index service.

    Fields:
        data: JSON data which specifies info about the data to be indexed.
            This is not the data that is actually indexed.
        context: the request context
        created: datetime object containing the time
            the job was created.
        not_before: datetime object containing the
            earliest time that the job should be
            started.
        start: datetime object containing the time
            the job started.
        end: datetime object containing the time
            the job ended.
        successful: boolean indicating that the job
            was successfully completed.
        retries_remaining: number of retries remaining
            for the job.
    """
    __tablename__ = "index_job"

    id = Column(Integer, primary_key=True)
    data = Column(Text(4096))
    context = Column(String(1024))
    created = Column(DateTime, server_default=func.current_timestamp())
    not_before = Column(DateTime, server_default=func.current_timestamp())
    start = Column(DateTime, nullable=True)
    end = Column(DateTime, nullable=True)
    owner = Column(String(1024), nullable=True)
    successful = Column(Boolean, nullable=True)
    retries_remaining = Column(Integer)

