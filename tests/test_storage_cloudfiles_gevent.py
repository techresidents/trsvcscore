import datetime
import logging
import unittest

import gevent 

import testbase
import trpycore.cloudfiles_gevent as cloudfiles
from trsvcscore.storage.cloudfiles import CloudfilesStorage, CloudfilesStorageFile
from trsvcscore.storage import exception


class TestCloudfilesStorage(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.DEBUG)
        cls.connection = cloudfiles.Connection(
                username="techresidents",
                api_key="6e472c9131df23960b230bfd0b936ade",
                servicenet=False)
        
        cls.container_name = "unittest_container"
        cls.container = cls.connection.create_container(
                container_name=cls.container_name)
        cls.container.make_private()

        cls.storage = CloudfilesStorage(
                connection=cls.connection,
                container_name=cls.container_name)

    @classmethod
    def tearDownClass(cls):
        cls.connection.delete_container(cls.container_name)
    
    def test_listdir(self):
        directories, files = self.storage.listdir()
        self.assertEqual(directories, [])
        self.assertEqual(files, [])

        #add a file / directory
        self.storage.save("test/test.txt", "This is a test")
        directories, files = self.storage.listdir()
        self.assertEqual(directories, ["test"])
        self.assertEqual(files, [])

        directories, files = self.storage.listdir("test/")
        self.assertEqual(directories, [])
        self.assertEqual(files, ["test.txt"])

        self.storage.delete("test/test.txt")

    def test_save(self):
        #save object
        name = "test.txt"
        data = "this is a test"
        self.storage.save(name, data)
        
        #open object
        storage_file = self.storage.open(name)
        self.assertEqual(storage_file.name(), name)
        self.assertEqual(storage_file.size(), len(data))
        self.assertEqual(storage_file.read(), data)
        storage_file.close()

        #delete object
        self.storage.delete(name)
    
    def test_exists(self):
        name = "test.txt"
        data = "this is a test"

        self.assertEqual(self.storage.exists(name), False)

        #save object
        self.storage.save(name, data)
        self.assertEqual(self.storage.exists(name), True)

        #delete object
        self.storage.delete(name)
        self.assertEqual(self.storage.exists(name), False)

    def test_modified_time(self):
        name = "test.txt"
        data = "this is a test"

        now = datetime.datetime.utcnow()
        gevent.sleep(1)
        self.assertEqual(self.storage.exists(name), False)

        #save object
        self.storage.save(name, data)
        self.assertEqual(self.storage.exists(name), True)
        modified_time = self.storage.modified_time(name)
        gevent.sleep(1)
        
        self.assertTrue(modified_time > now)
        self.assertTrue(modified_time < datetime.datetime.utcnow())

        #delete object
        self.storage.delete(name)
        self.assertEqual(self.storage.exists(name), False)

    def test_url(self):
        #save object
        name = "test.txt"
        data = "this is a test"
        self.storage.save(name, data)

        url = self.storage.url(name)
        #self.assertEqual(url, None)

        self.storage.delete(name)


class TestCloudfilesStorageWithLocationBase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.DEBUG)
        cls.connection = cloudfiles.Connection(
                username="techresidents",
                api_key="6e472c9131df23960b230bfd0b936ade",
                servicenet=False)
        
        cls.container_name = "unittest_container"
        cls.container = cls.connection.create_container(
                container_name=cls.container_name)
        cls.container.make_private()

        cls.storage = CloudfilesStorage(
                connection=cls.connection,
                container_name=cls.container_name,
                location_base="unittest_location")

    @classmethod
    def tearDownClass(cls):
        cls.connection.delete_container(cls.container_name)
    
    def test_listdir(self):
        directories, files = self.storage.listdir()
        self.assertEqual(directories, [])
        self.assertEqual(files, [])

        #add a file / directory
        self.storage.save("test/test.txt", "This is a test")
        directories, files = self.storage.listdir()
        self.assertEqual(directories, ["test"])
        self.assertEqual(files, [])

        directories, files = self.storage.listdir("test/")
        self.assertEqual(directories, [])
        self.assertEqual(files, ["test.txt"])

        self.storage.delete("test/test.txt")

    def test_save(self):
        #save object
        name = "test.txt"
        data = "this is a test"
        self.storage.save(name, data)
        
        #open object
        storage_file = self.storage.open(name)
        self.assertEqual(storage_file.name(), name)
        self.assertEqual(storage_file.size(), len(data))
        self.assertEqual(storage_file.read(), data)
        storage_file.close()

        #delete object
        self.storage.delete(name)
    
    def test_exists(self):
        name = "test.txt"
        data = "this is a test"

        self.assertEqual(self.storage.exists(name), False)

        #save object
        self.storage.save(name, data)
        self.assertEqual(self.storage.exists(name), True)

        #delete object
        self.storage.delete(name)
        self.assertEqual(self.storage.exists(name), False)

    def test_url(self):
        #save object
        name = "test.txt"
        data = "this is a test"
        self.storage.save(name, data)

        url = self.storage.url(name)
        #self.assertEqual(url, None)

        self.storage.delete(name)

class TestCloudfilesStorageCdn(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.DEBUG)
        cls.connection = cloudfiles.Connection(
                username="techresidents",
                api_key="6e472c9131df23960b230bfd0b936ade",
                servicenet=False)
        
        cls.container_name = "unittest_container"
        cls.container = cls.connection.create_container(
                container_name=cls.container_name)
        cls.container.make_public()

        cls.storage = CloudfilesStorage(
                connection=cls.connection,
                container_name=cls.container_name)

    @classmethod
    def tearDownClass(cls):
        cls.connection.delete_container(cls.container_name)
    
    def test_url(self):
        #save object
        name = "test.txt"
        data = "this is a test"
        self.storage.save(name, data)

        url = self.storage.url(name)
        self.assertIsNotNone(url)
        self.assertTrue(url.startswith("http:"))

        url = self.storage.url(name, streaming=True)
        self.assertIsNotNone(url)
        self.assertTrue(url.startswith("http:"))

        url = self.storage.url(name, ssl=True)
        self.assertIsNotNone(url)
        self.assertTrue(url.startswith("https:"))

        self.storage.delete(name)

class TestCloudfilesStorageFile(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.DEBUG)
        cls.connection = cloudfiles.Connection(
                username="techresidents",
                api_key="6e472c9131df23960b230bfd0b936ade",
                servicenet=False)
        
        cls.container_name = "unittest_container"
        cls.container = cls.connection.create_container(
                container_name=cls.container_name)
        cls.container.make_public()

        cls.storage = CloudfilesStorage(
                connection=cls.connection,
                container_name=cls.container_name)

    @classmethod
    def tearDownClass(cls):
        cls.connection.delete_container(cls.container_name)

    def test_basic(self):
        name = "test.txt"
        mode = "wb"
        data = "this is a test."
        
        #open for writing
        storage_file = CloudfilesStorageFile(self.container, name, mode)
        storage_file.write(data)

        self.assertTrue(self.storage.exists(name))
        self.assertEqual(storage_file.name(), name)
        self.assertEqual(storage_file.mode(), mode)
        self.assertEqual(storage_file.size(), len(data))
        
        #reads not allowed in write mode
        with self.assertRaises(exception.FileOperationNotAllowed):
            storage_file.read()

        #multiple writes not allowed
        with self.assertRaises(exception.FileOperationNotAllowed):
            storage_file.write(data)

        #open in read mode
        storage_file.open("r")
        self.assertEqual(storage_file.read(), data)

        #close file
        storage_file.close()
        
        #operations not allowed on closed files
        with self.assertRaises(exception.FileNotOpen):
            storage_file.read()
        with self.assertRaises(exception.FileNotOpen):
            storage_file.write(data)

        #delete 
        self.storage.delete(name)

    def test_invalid_open(self):
        name = "test.txt"

        with self.assertRaises(exception.InvalidArgument):
            CloudfilesStorageFile(self.container, name, "rw")

    def test_partial_read(self):
        name = "test.txt"
        mode = "wb"
        data = "this is a test."
        
        #open for writing
        storage_file = CloudfilesStorageFile(self.container, name, mode)
        storage_file.write(data)

        self.assertTrue(self.storage.exists(name))
        self.assertEqual(storage_file.name(), name)
        self.assertEqual(storage_file.mode(), mode)
        self.assertEqual(storage_file.size(), len(data))

        #open in read mode
        storage_file.open("r")
        self.assertEqual(storage_file.read(1), data[0])
        self.assertEqual(storage_file.read(2), data[1:3])
        self.assertEqual(storage_file.read(), data[3:])
        self.assertEqual(storage_file.read(), "")

        #delete 
        self.storage.delete(name)

if __name__ == "__main__":
    unittest.main()
