from sqlalchemy import Boolean, Column, Integer, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from trsvcscore.db.models.base import Base
from trsvcscore.db.models.accounts_models import User


class Notification(Base):
    """Notification data model.

    The 'token' and 'context' are considered
    together for a notification to be unique.

    Fields:
        created: datetime object containing the time
            the Notification was created.
        token: notification ID. Used to allow creators of
            Notification objects to specify an ID.
        context: the request context
        priority: Priority level integer
        recipients: User data model objects
        subject: the notification subject
        html_text: html notification body
        plain_text: plain text notification body
    """
    __tablename__ = "notification"
    __table_args__ = (UniqueConstraint('token', 'context'),
        )

    id = Column(Integer, primary_key=True)
    created = Column(DateTime, server_default=func.current_timestamp())
    token = Column(String(1024))
    context = Column(String(1024))
    priority = Column(Integer)
    recipients = relationship(User, secondary=lambda: NotificationUser.__table__)
    subject = Column(String(1024))
    html_text = Column(Text, nullable=True)
    plain_text = Column(Text, nullable=True)


class NotificationUser(Base):
    """Notification User data model.

    Linking table for notifications and users.
    """
    __tablename__ = "notification_user"

    id = Column(Integer, primary_key=True)
    notification_id = Column(Integer, ForeignKey("notification.id"))
    user_id = Column(Integer, ForeignKey("accounts_user.id"))

    notification = relationship(Notification)
    user = relationship(User)


class NotificationJob(Base):
    """NotificationJob data model.

    Represents a job for the notification service.

    Fields:
        notification: Notification data model object
        recipient: User data model object
        priority: Priority level integer
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
    __tablename__ = "notification_job"

    id = Column(Integer, primary_key=True)
    notification_id = Column(Integer, ForeignKey("notification.id"))
    recipient_id = Column(Integer, ForeignKey("accounts_user.id"))
    priority = Column(Integer)
    created = Column(DateTime, server_default=func.current_timestamp())
    not_before = Column(DateTime, server_default=func.current_timestamp())
    start = Column(DateTime, nullable=True)
    end = Column(DateTime, nullable=True)
    owner = Column(String(1024), nullable=True)
    successful = Column(Boolean, nullable=True)
    retries_remaining = Column(Integer)

    notification = relationship(Notification, backref="notification_jobs")
    recipient = relationship(User)

