import datetime
import logging
import os
import shutil
import time
import unittest

import testbase
from trsvcscore.storage.filesystem import FileSystemStorage, FileSystemStorageFile
from trsvcscore.storage import exception


class TestFileSystemStorage(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.DEBUG)
        cls.location = "/tmp/unittest"
        cls.storage = FileSystemStorage(
                location=cls.location)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.location)
    
    def test_listdir(self):
        directories, files = self.storage.listdir()
        self.assertEqual(directories, [])
        self.assertEqual(files, [])

        #add a file / directory
        self.storage.save("test/test.txt", "This is a test")
        directories, files = self.storage.listdir()
        self.assertEqual(directories, ["test"])
        self.assertEqual(files, [])

        directories, files = self.storage.listdir("test")
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
        time.sleep(1)
        self.assertEqual(self.storage.exists(name), False)

        #save object
        self.storage.save(name, data)
        self.assertEqual(self.storage.exists(name), True)
        modified_time = self.storage.modified_time(name)
        time.sleep(1)
        
        self.assertTrue(modified_time > now)
        self.assertTrue(modified_time < datetime.datetime.utcnow())

        #delete object
        self.storage.delete(name)
        self.assertEqual(self.storage.exists(name), False)

    def test_path(self):
        #save object
        name = "test.txt"
        data = "this is a test"
        self.storage.save(name, data)
        
        path = self.storage.path(name)
        self.assertEqual(path, os.path.join(self.location, name))

        self.storage.delete(name)

    def test_url(self):
        #save object
        name = "test.txt"
        data = "this is a test"
        self.storage.save(name, data)
        
        with self.assertRaises(exception.NotImplemented):
            self.storage.url(name)

        self.storage.delete(name)


class TestFileSystemStorageFile(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.DEBUG)
        cls.location = "/tmp/unittest"
        cls.storage = FileSystemStorage(
                location=cls.location)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.location)

    def test_basic(self):
        name = "test.txt"
        mode = "wb"
        data = "this is a test."
        
        #open for writing
        storage_file = FileSystemStorageFile(self.location, name, mode)
        storage_file.write(data)

        self.assertTrue(self.storage.exists(name))
        self.assertEqual(storage_file.name(), name)
        self.assertEqual(storage_file.mode(), mode)

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

    def test_partial_read(self):
        name = "test.txt"
        mode = "wb"
        data = "this is a test."
        
        #open for writing
        storage_file = FileSystemStorageFile(self.location, name, mode)
        storage_file.write(data)
        storage_file.close()

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
