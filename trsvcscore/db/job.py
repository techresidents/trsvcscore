import logging
import threading
import Queue

from sqlalchemy.sql import func

from trpycore.timezone import tz

class QueueEmpty(Exception):
    """Queue empty exception."""
    pass

class QueueStopped(Exception):
    """Queue stopped exception."""
    pass

class JobOwned(Exception):
    """Job owned exception."""
    pass

class DatabaseJob(object):
    """Database job class.

    DatabaseJob provides a convenient context manager wrapper
    for database models belonging to database tables acting
    as job queues.     

    Upon entering the context manager the model is updated with
    the values returned from self._start_update_values().

    Upon exiting the context manager the model is update with
    the values returned from self._end_update_values(),
    if not exception is raised during processed, or
    self._abort_update_values() otherwise.

    This class is easily designed to be customized for various tables
    by subclassing and extending self._start_update_values(),
    self._end_update_values(), and self._abort_update_values().

    By default, the following updates will occur:
        Context Manager Enter:
            model.owner = self.owner
            model.start = tz.utcnow()
        Context Manager Exit (No Exception):
            model.successful = True
            model.end = tz.utcnow()
        Context Manager Exit (Exception):
            model.successful = False
            model.end = tz.utcnow()
    
    Note that this class is not typically instantiated directly,
    instead it should be used in conjunction with DatabaseJobQueue.

    See DatabaseJobQueue for usage examples.
    """

    def __init__(self, owner, model_class, model_id,  db_session_factory):
        """DatabaseJob constructor.

        Args:
            owner: string identifying the owner of this job. This value
                will be set on the model and the database updated,
                upon successfully entering the context manager.
            model_class: SQLAlchemy database model class
            model_id: model primary key
            db_session_factory: SQLAlchemy database session factory
                in the form of a method requiring no parameters and
                returning an instance of a SQLAlchemy session.
        """
        self.owner = owner
        self.model_class = model_class
        self.model_id = model_id
        self.model = None
        self.db_session_factory = db_session_factory
        self.db_session = None
    
    def __enter__(self):
        """Context manager enter method.

        Raises:
            JobOwned if the job is already owned.
        """
        #create session with expire_on_commit set to False,
        #so that we can detach self.model for use outside
        #of the context manager. If expire_on_commit were
        #set to the default value of True, self.model would
        #not be available for use as a detached model following
        #without first being refresh()'d.
        self.db_session = self.db_session_factory(expire_on_commit=False)
        self.model = self._start()
        return self.model
    
    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit method.

        Args:
            exc_type: exception type if an exception was raised
                within the scope of the context manager, None otherwise.
            exc_value: exception value if an exception was raised
                within the scope of the context manager, None otherwise.
            traceback: exception traceback if an exception was raised
                within the scope of the context manager, None otherwise.
        """
        try:
            if exc_type is not None:
                self._abort()
            else:
                self._end()
        finally:
            if self.db_session:
                if self.model:
                    #Note that refresh() is no longer needed now that
                    #the session is being created with expire_on_commit
                    #set to false. Without this, refresh() is neeeded
                    #to detach self.model so it can be accessed once the
                    #context manager block is exited.
                    #self.db_session.refresh(self.model)
                    self.db_session.expunge(self.model)
                self.db_session.close()
                self.db_session = None
    
    def _start_query_filters(self):
        """SQLAlchemy query filters to be applied when job is started.

        Returns:
            list of SQLAlchemy filters
        """
        filters = []
        if hasattr(self.model_class, "id"):
            filters.append(self.model_class.id == self.model_id)
        if hasattr(self.model_class, "owner"):
            filters.append(self.model_class.owner == None)
        return filters

    def _start_update_values(self):
        """Model attributes/values to be updated when job is started.

        Returns:
            dict of model {attribute: value} to be updated when
            the job is started.
        """
        update_values = {}
        if hasattr(self.model_class, "owner"):
            update_values["owner"] = self.owner
        if hasattr(self.model_class, "start"):
            update_values["start"] = tz.utcnow()
        return update_values

    def _end_update_values(self):
        """Model attributes/values to be updated when job is ended.

        Returns:
            dict of model {attribute: value} to be updated when
            the job is ended.
        """
        update_values = {}
        if hasattr(self.model_class, "end"):
            update_values["end"] = func.current_timestamp()
        if hasattr(self.model_class, "successful"):
            update_values["successful"] = True
        return update_values

    def _abort_update_values(self):
        """Model attributes/values to be updated when job is aborted.
        
        A job is considered to be aborted if an exception is raised
        within the scope of the context manager.

        Returns:
            dict of model {attribute: value} to be updated when
            the job is aborted.
        """
        update_values = {}
        if hasattr(self.model_class, "end"):
            update_values["end"] = func.current_timestamp()
        if hasattr(self.model_class, "successful"):
            update_values["successful"] = False
        return update_values

    def _start_query(self, db_session):
        """Job start query.
        
        Returns:
            SQLAlchemy Query object.
        """
        query = db_session.query(self.model_class)
        for filter in self._start_query_filters():
            query = query.filter(filter)
        return query

    def _start(self):
        """Start database job."""
        # This query.update generates the following sql:
        # UPDATE <table> SET owner='<owner>' WHERE
        # <table>.id = <id> AND <table>.owner IS NULL
        rows_updated = self._start_query(self.db_session).\
            update(self._start_update_values())

        if not rows_updated:
            raise JobOwned("%s(id=%s) already owned") % (self.model_class, self.model_id)
        
        self.db_session.commit()

        model = self.db_session.query(self.model_class)\
                .get(self.model_id)
        
        return model

    def _end(self):
        """End database job."""
        for attribute, value in self._end_update_values().items():
            if hasattr(self.model_class, attribute):
                setattr(self.model, attribute, value)
        self.db_session.commit()

    def _abort(self):
        """Abort database job."""
        for attribute, value in self._abort_update_values().items():
            if hasattr(self.model_class, attribute):
                setattr(self.model, attribute, value)
        self.db_session.commit()


class DatabaseJobQueue(object):
    """Database job queue.
    
    DatabaseJobQueue is a convenient utility for working with
    database models belonging to database tables acting as 
    job queues.

    Once started, DatabaseJobQueue will poll the table specified
    through the model_class for new jobs. New jobs will be
    wrapped in a DatabaseJob object, and added to a thread-safe
    queue for consumption.

    The DatabaseJob object serves as a context manager, through
    which the job should be consumed. It ensures that the 
    job is properly updated before and after job processing.
    
    See DatabaseJob for the details on how the database model
    will be updated.  If the exact attributes updated by DatabaseJob 
    do not match your model you can subclass Databasejob and pass it to
    DatabaseJobQueue through the db_job_class constructor
    argument.

    Example usage:
        db_queue = DatabaseJobQueue(
            owner="archivesvc",
            model_class=ChatArchiveJob,
            db_session_factory=db_session_factory)
        
        while True:
            try:
                with db_queue.get() as job:
                    #upon entering context manager job is properly owned
                    #if the context manager is exited successfully the 
                    #job will be updated to indicate success.
                    #if the context manager is exited through an exception
                    #the job be updated to indicate failutre.
                    process(job)
            except JobOwned:
                #job already owned
                pass
            except QueueStopped:
                break
            except Exception:
                #failure during processing.
                #handle error and possibly create new job in db to retry.
    """
    
    #Stop item to signal to blocked waiters that the queue is being stopped.
    STOP_ITEM = object()

    def __init__(self,
            owner,
            model_class,
            db_session_factory,
            poll_seconds=60,
            db_job_class=None):
        """DatabaseJobQueue constructor.

        Args:
            owner: string identifying the owner of returned jobs.
                This value will be set on the model and the database
                updated, upon successfully entering the returned
                DatabaseJob object's context manager.
            model_class: SQLAlchemy database model class
            db_session_factory: SQLAlchemy database session factory
                in the form of a method taking no parameters and
                returning an instance of a SQLAlchemy Session object.
            poll_seconds: optional time in seconds to poll the database
                for new jobs.
            db_job_class: optional database job class to wrap job
                model in prior to returning it. If not specified
                this defaults to DatabaseJob.
        """
        self.owner = owner
        self.model_class = model_class
        self.db_session_factory = db_session_factory
        self.poll_seconds = poll_seconds
        self.db_job_class = db_job_class or DatabaseJob
        self.queue = Queue.Queue()
        self.exit = threading.Event()
        self.running = False
        self.thread = None
    
    def _query_filters(self):
        """Get job poll query filters.

        Returns:
            list of SQLAlchemy filters to be applied to the job
            poll query.
        """
        filters = []
        if hasattr(self.model_class, "owner"):
            filters.append(self.model_class.owner == None)
        if hasattr(self.model_class, "start"):
            filters.append(self.model_class.start == None)
        if hasattr(self.model_class, "not_before"):
            filters.append(self.model_class.not_before <= func.current_timestamp())
        return filters

    def _query(self, db_session):
        """Get job poll query.

        Returns:
            SQLAlchemy Query object to be used to find new jobs.
        """
        query = db_session.query(self.model_class)
        for filter in self._query_filters():
            query = query.filter(filter)
        if hasattr(self.model_class, "priority"):
            query.order_by(self.model_class.priority)
        return query
    
    def _add_stop_items(self):
        """Helper method to add STOP_ITEM's to queue.

        STOP_ITEM's are added to self.queue to unblock
        current waiters on the queue.
        """
        for i in xrange(100):
            self.queue.put(self.STOP_ITEM)

    def _remove_stop_items(self):
        """Helper method to remove STOP_ITEM's from queue."""
        non_stop_items = []
        try:
            while True:
                item = self.queue.get(block=False)
                if item is not self.STOP_ITEM:
                    non_stop_items.append(item)
        except Queue.Empty:
            for item in non_stop_items:
                self.queue.put(item)

    def get(self, block=True, timeout=None):
        """Get new database job.
        
        Args:
            block: optional boolean indicating if the
                method should block until new a new
                job becomes available. 
            timeout: optional timeout in seconds, used
                in conjunction with block=True, to
                specify the maximum amount of time
                the method should block before raising
                a QueueEmpty exception.
        Returns:
            DatabaseJob object or an instance of self.db_job_class
            if specified.
        Raises:
            QueueStopped: if queue is stopped.
            QueueEmpty: if no items are available and
                the get() is not blocking or timeout
                is exceeded.
        """
        if not self.running:
            raise QueueStopped()

        try:
            result = self.queue.get(block, timeout)
            if result is self.STOP_ITEM:
                raise QueueStopped()
            return result
        except Queue.Empty:
            raise QueueEmpty()

    def start(self):
        """Start polling database for new jobs."""
        if not self.running:
            self.exit.clear()
            self._remove_stop_items()
            self.running = True
            self.thread = threading.Thread(target=self.run)
            self.thread.start()

    def run(self):
        """Database polling method."""

        session = self.db_session_factory()

        while self.running:
            try:
                for job in self._query(session):
                    database_job = self.db_job_class(
                            owner=self.owner,
                            model_class=self.model_class,
                            model_id=job.id,
                            db_session_factory=self.db_session_factory)
                    self.queue.put(database_job)
                session.commit()

            except Exception as error:
                session.rollback()
                logging.exception(error)
            finally:
                self.exit.wait(self.poll_seconds)

        self.running = False
        session.close()
    
    def stop(self):
        """Stop polling database for new jobs.

        This will result in a QueueStopped exception be raised
        for waiters blocked in a get() method.
        """
        if self.running:
            self.running = False
            self.exit.set()
            self._add_stop_items()

    def join(self, timeout=None):
        """Join database queue.

        Args:
            timeout: optional timeout in seconds.
        """
        if self.thread is not None:
            self.thread.join(timeout)
