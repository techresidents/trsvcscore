import datetime
import logging
import threading
import time
import unittest
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import testbase
from trpycore.timezone import tz
from trsvcscore.db.job import DatabaseJobQueue, QueueEmpty, QueueStopped
from trsvcscore.db.models import ChatArchiveJob

#Database settings
DATABASE_HOST = "localdev"
DATABASE_NAME = "localdev_techresidents"
DATABASE_USERNAME = "techresidents"
DATABASE_PASSWORD = "techresidents"
DATABASE_CONNECTION = "postgresql+psycopg2://%s:%s@/%s?host=%s" % (DATABASE_USERNAME, DATABASE_PASSWORD, DATABASE_NAME, DATABASE_HOST)

class TestDatabaseJob(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.DEBUG)
        cls.engine = create_engine(DATABASE_CONNECTION)
        cls.db_session_factory = sessionmaker(bind=cls.engine)
        cls.db_queue = DatabaseJobQueue(
                owner="unittest",
                model_class = ChatArchiveJob,
                db_session_factory=cls.db_session_factory,
                poll_seconds=1)
        cls.db_queue.start()

    @classmethod
    def tearDownClass(cls):
        cls.db_queue.stop()
    
    @contextmanager
    def _archive_job(self, chat_session_id, not_before=None):
        not_before = not_before or tz.utcnow()
        try:
            session = self.db_session_factory()
            job = ChatArchiveJob(
                    chat_session_id=chat_session_id,
                    created=tz.utcnow(),
                    not_before=not_before,
                    retries_remaining=0)
            session.add(job)
            session.commit()
            yield session, job
        except Exception as error:
            logging.exception(error)
            raise
        finally:
            if session:
                if job:
                    session.delete(job)
                    session.commit()
                session.close()
        
    def test_get(self):
        test_start_time = tz.utcnow()

        with self.assertRaises(QueueEmpty):
            self.db_queue.get(False)

        with self._archive_job(1) as (session, job):
            with self.db_queue.get(True, 10) as db_job:
                self.assertEqual(job.id, db_job.id)
                self.assertEqual(job.chat_session_id, db_job.chat_session_id)
                self.assertEqual(job.created, db_job.created)
                self.assertEqual(db_job.owner, "unittest")
                self.assertIsNone(db_job.end)
                self.assertIsNone(db_job.successful)
                self.assertTrue(tz.utcnow() > db_job.start)
                self.assertTrue(test_start_time < db_job.start)
            session.refresh(job)
            self.assertTrue(job.successful)
            self.assertTrue(job.start < job.end)
    
    def test_get_failed_processing(self):
        test_start_time = tz.utcnow()

        with self.assertRaises(QueueEmpty):
            self.db_queue.get(False)

        with self._archive_job(1) as (session, job):
            try:
                with self.db_queue.get(True, 10) as db_job:
                    self.assertEqual(job.id, db_job.id)
                    self.assertEqual(job.chat_session_id, db_job.chat_session_id)
                    self.assertEqual(job.created, db_job.created)
                    self.assertEqual(db_job.owner, "unittest")
                    self.assertIsNone(db_job.end)
                    self.assertIsNone(db_job.successful)
                    self.assertTrue(tz.utcnow() > db_job.start)
                    self.assertTrue(test_start_time < db_job.start)
                    raise ValueError()
            except:
                pass
            session.refresh(job)
            self.assertFalse(job.successful)
            self.assertTrue(job.start < job.end)

    def test_not_before(self):
        not_before = tz.utcnow() + datetime.timedelta(seconds=5)

        with self._archive_job(1, not_before) as (session, job):
            with self.assertRaises(QueueEmpty):
                self.db_queue.get(False)

            with self.db_queue.get(True, 10) as db_job:
                self.assertEqual(job.id, db_job.id)
                self.assertEqual(job.chat_session_id, db_job.chat_session_id)
                self.assertEqual(job.created, db_job.created)
                self.assertEqual(db_job.owner, "unittest")
                self.assertIsNone(db_job.end)

            session.refresh(job)
            self.assertTrue(job.successful)
            self.assertTrue(job.start < job.end)
    
    def test_stop(self):
        def delayed_stop():
            time.sleep(1)
            self.db_queue.stop()
        
        threading.Thread(target=delayed_stop).start()
        with self.assertRaises(QueueStopped):
            self.db_queue.get(True, 10)

        self.db_queue.start()

if __name__ == "__main__":
    unittest.main()
