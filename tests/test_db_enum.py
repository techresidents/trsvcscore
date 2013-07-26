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
from trsvcscore.db.enum import Enum
from trsvcscore.db import models

#Database settings
DATABASE_HOST = "localdev"
DATABASE_NAME = "localdev_techresidents"
DATABASE_USERNAME = "techresidents"
DATABASE_PASSWORD = "techresidents"
DATABASE_CONNECTION = "postgresql+psycopg2://%s:%s@/%s?host=%s" % (DATABASE_USERNAME, DATABASE_PASSWORD, DATABASE_NAME, DATABASE_HOST)

class TestDatabaseEnum(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.DEBUG)
        cls.engine = create_engine(DATABASE_CONNECTION)
        cls.db_session_factory = sessionmaker(bind=cls.engine)

    @classmethod
    def tearDownClass(cls):
        pass
    
    def test_db_enum(self):

        class TopicTypeEnum(Enum):
            model_class = models.TopicType
            key_column = "name"
            value_column = "id"
            db_session_factory = self.db_session_factory

        self.assertEqual(TopicTypeEnum.DEVELOPER, 1)
        self.assertEqual(TopicTypeEnum.EMPLOYER, 2)
        self.assertEqual(len(TopicTypeEnum.KEYS_TO_VALUES), 2)
        self.assertEqual(len(TopicTypeEnum.VALUES_TO_KEYS), 2)
        self.assertEqual(TopicTypeEnum.KEYS_TO_VALUES["DEVELOPER"], 1)
        self.assertEqual(TopicTypeEnum.KEYS_TO_VALUES["EMPLOYER"], 2)
        self.assertEqual(TopicTypeEnum.VALUES_TO_KEYS[1], "DEVELOPER")
        self.assertEqual(TopicTypeEnum.VALUES_TO_KEYS[2], "EMPLOYER")

if __name__ == "__main__":
    unittest.main()
