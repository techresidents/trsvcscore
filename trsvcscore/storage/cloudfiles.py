from __future__ import absolute_import 

import datetime
import logging
import mimetypes
import os
import Queue

from cloudfiles.errors import NoSuchObject

from trpycore.pool.queue import QueuePool
from trsvcscore.storage.base import Storage, StorageFile, StorageFileMode
from trsvcscore.storage import exception


class CloudfilesStorageFile(StorageFile):
    """Rackspace cloudfiles storage file.

    StorageFile objects should not typically be instantiated directly. Instead
    the Storage object backend should be used in order to obtain a StorageFile
    object.
    
    All StorageFile names are relative. For example,
    'me.jpeg', or 'photos/me.jpeg' are okay, but not '/mypath/photos/me.jpeg'.
    This is intentional so that the names can be persisted if needed,
    and still allow for Storage backends to be switched without too
    much trouble.
    """
    
    def __init__(self, container, name, mode, content_type=None, location_base=None):
        """CloudfilesStorageFile constructor.

        Args:
            container: cloudfiles.Container object
            name: relative filename
            mode: file mode, i.e. 'rb'
            content_type: optional mime content type. If
                not provided the mime type will be
                guessed.
            location_base: optional location within the container
                where the relative filename is located.
                Note that the location_base is not exposed
                to applications, for example in the
                name() method.
        """
        super(CloudfilesStorageFile, self).__init__(name, mode)
        self.container = container
        self.location_base = location_base or ""
        self.content_type = content_type or mimetypes.guess_type(self._name)[0]
        
        self.location = "%s%s" % (self.location_base, name)
        self.file_mode = None
        self.object = None
        self.offset = 0
        
        self.open(mode)
    
    def _validate_file_mode(self, mode):
        """Validate file mode.
        
        Currently we only support read or write mode, not
        both at the same time.

        Args:
            mode: file mode, i.e. 'rb'
        Returns:
            StorageFileMode object.
        """
        file_mode = StorageFileMode(mode)
        if file_mode.append:
            raise exception.InvalidArgument("append mode unsupported")
        elif file_mode.readable and file_mode.writable:
            raise exception.InvalidArgument("read-write mode unsupported")
        return file_mode

    def name(self):
        """Get relative file name.

        Returns:
            relative filename, i.e. 'photos/me.jpeg'
        """
        return self._name

    def mode(self):
        """Get file mode.

        Returns:
            file mode, i.e. 'rb'
        """
        return self._mode

    def size(self):
        """Get file size.

        Returns:
            file size in bytes.
        Raises:
            StorageException
        """
        return self.object.size

    def open(self, mode=None):
        """Open/reopen file in the given mode.
        
        Args:
            mode: optional file mode, i.e. 'rb'
        Raises:
            StorageException

        Reopens the file in the specified mode if provided.
        Otherwise the file is reopened using the same mode.
        Reopening the file will reset the file pointer to
        the begining of the file.
        """
        if mode is not None:
            self.file_mode = self._validate_file_mode(mode)
            self._mode = mode

        try:
            self.object = self.container.get_object(self.location)
            self.offset = 0
        except NoSuchObject:
            if self.file_mode.create:
                self.object = self.container.create_object(self.location)
            else:
                raise exception.FileDoesNotExist("'%s' does not exist" % self._name)
        except Exception as error:
            logging.exception(error)
            raise exception.StorageException(str(error))

    def read(self, size=None):
        """Read size bytes from file.
        
        Args:
            size: optional number of bytes to read.
                  If not provided the entire file
                  will be read.
        Returns:
            file data as a string.
        Raises:
            StorageException
        """
        if self.object is None:
            raise exception.FileNotOpen("file not open")
        elif not self.file_mode.readable:
            raise exception.FileOperationNotAllowed("file not opened in read mode")
        
        try:
            if self.offset >= self.size():
                result = ""
            else:
                result = self.object.read(
                        size=size or self.size() - self.offset,
                        offset=self.offset)
                self.offset += size or len(result)
        except Exception as error:
            logging.exception(error)
            raise exception.FileOperationFailed(str(error))
        return result

    def write(self, data):
        """Write data to file.

        Args:
            data: string of file like object containing
                  a read(n) method.
        Raises:
            StorageException
        """
        if self.object is None:
            raise exception.FileNotOpen("file not open")
        elif not self.file_mode.writable:
            raise exception.FileOperationNotAllowed("file not opened in write mode")
        elif self.offset != 0:
            raise exception.FileOperationNotAllowed("writes with non-zero offset not permitted")

        try:
            if self.content_type:
                self.object.content_type = self.content_type
            self.object.write(data)
            self.offset = self.object.size
        except Exception as error:
            logging.exception(error)
            raise exception.FileOperationFailed(str(error))
    
    def seek(self, offset, whence=0):
        """Move file pointer to specified offset.

        Args:
            offset: integer offset in bytes relative to whence
            whence: os.SEEK_SET (0) - relative to beginning of file
                    os.SEEK_CUR (1) - relative to current position
                    os.SEEK_END (2) - relative to end of file
        Raises:
            StorageException
        """
        if self.file_mode.writable:
            raise exception.FileOperationNotAllowed("seek not permitted on files opened in write mode")

        if whence == os.SEEK_SET:
            self.offset = offset
        elif whence == os.SEEK_CUR:
            self.offset += offset
        elif whence == os.SEEK_END:
            self.offset += offset
        else:
            raise exception.InvalidArgument("invalid whence value")
    
    def tell(self):
        """Return file pointer offset.

        Returns:
            file pointer offset.
        Raises:
            StorageException
        """
        return self.offset

    def close(self):
        """Close the file."""
        self.object = None
        self.offset = 0


class CloudfilesStorage(Storage):
    """Rackspace cloudfiles storage backend.

    Storage backends provided an interface for accessing, file
    like, StorageFile objects. Each StorageFile object is
    identified by a relative name.
    
    Note that in order for Storage backends to remain swappable,
    it is critical that names be relative. For example, the names 
    'me.jpeg' or 'photos/me.jpeg' are okay, but '/fullpath/photos.jpeg'
    is not. The idea is to use logical, relative names throughout
    applications, so that this name can be safely persisted, while
    still allowing for the Storage backend to be swapped out without
    too much trouble.
    """

    def __init__(self, connection, container_name, location_base=None):
        """CloudfilesStorage constructor.

        Args:
            connection: cloudfiles.Connection object
            container_name: cloud files container name
            location_base: optional location within the container
                where files should be stored. Note that the
                location_base will not be exposed to applications,
                for example, in the relative filename returned
                save().
        """
        self.connection = connection
        self.container_name = container_name
        self.container = self.connection.get_container(container_name)
        self.location_base = location_base
        
        #normalize location base
        if self.location_base is not None:
            if self.location_base.startswith("/"):
                self.location_base = self.location_base[1:]
            if not self.location_base.endswith("/"):
                self.location_base += "/"
    
    def _name_to_location(self, name):
        """Convert relative filename to container location.
        
        Args:
            name: relative filename.

        Returns:
            location of file within the container.
        """
        result = name
        if self.location_base:
            result = "%s%s" % (self.location_base, name)
        return result

    def listdir(self, path=None):
        """Get directory,file listing.

        Args:
            path: optional relative path to filter.
        Returns:
            (list_of_directories, list_of_files) tuple
        Raises:
            StorageException
        """
        directories = []
        files = []
        
        #Convert path to container location
        path = self._name_to_location(path or "")

        #path must end in / if provided
        if path and not path.endswith("/"):
            path += "/"
        elif not path:
            path = ""
        path_length = len(path)

        objects = self.container.list_objects(prefix=path, delimiter="/")

        for entry in objects:
            if entry.endswith("/"):
                directories.append(entry[path_length:-1])
            else:
                files.append(entry[path_length:])

        return directories, files

    def exists(self, name):
        """Check if storage file exists.

        Args:
            name: relative filename
        Returns:
            boolean indicating if storage file exists.
        Raises:
            StorageException
        """
        result = False
        try:
            location = self._name_to_location(name)
            self.container.get_object(location)
            result = True
        except NoSuchObject:
            pass
        except Exception as error:
            logging.exception(error)
            raise exception.StorageException(str(error))

        return result

    def modified_time(self, name):
        """File modification utc datetime object.

        Args:
            name: relative filename
        Returns:
            file modification utc datetime object.
        Raises:
            StorageException
        """
        try:
            location = self._name_to_location(name)
            last_modified = self.container.get_object(location).last_modified
            return datetime.datetime.strptime(last_modified, '%a, %d %b %Y %H:%M:%S %Z')
        except NoSuchObject:
            raise exception.FileDoesNotExist("'%s' does not exist" % name)
        except Exception as error:
            logging.exception(error)
            raise exception.StorageException(str(error))

    def open(self, name, mode='rb'):
        """Open storage file.

        Args:
            name: relative filename
            mode: optional file mode
        Returns:
            StorageFile object.
        Raises:
            StorageException
        """
        return CloudfilesStorageFile(
                container=self.container,
                name=name,
                mode=mode,
                location_base=self.location_base)

    def save(self, name, data, content_type=None):
        """Save and create new storage file.

        Args:
            name: relative filename
            data: string or file-like object with a
                  read(n) method.
            content_type: optional mime content type.
        Raises:
            StorageException
        """
        if self.exists(name):
            raise exception.FileOperationFailed("'%s' already exists" % name)

        with CloudfilesStorageFile(
                container=self.container,
                name=name,
                mode='w',
                location_base=self.location_base) as f:
            f.write(data)

        return name

    def size(self, name):
        """Get storage file size.

        Args:
            name: relative filename
        Returns:
            file size in bytes.
        Raises:
            StorageException
        """
        location = self._name_to_location(name)
        return self.container.get_object(location).size
    
    def path(self, name):
        """Get local filesystem path of storage file.

        Args:
            name: relative filename
        Returns:
            local filesystem path to file.
        Raises:
            StorageException
        """
        raise exception.NotImplemented()

    def url(self, name, ssl=False, streaming=False):
        """Get public url of storage file.

        Args:
            name: relative filename
            ssl: optional flag indicating that an
                 ssl url should be returned.
            streaming: optional flag indicating 
                that a streaming url should
                be returned.
        Returns:
            url to file.
        Raises:
            StorageException
        """
        if ssl and streaming:
            raise exception.InvalidArgument("ssl and streaming are mutually exclusive")

        result = None
        if self.container.is_public():
            location = self._name_to_location(name)
            if ssl:
                result = "%s/%s" % (self.container.public_ssl_uri(), location)
            elif streaming:
                result = "%s/%s" % (self.container.public_streaming_uri(), location)
            else:
                result = "%s/%s" % (self.container.public_uri(), location)

        return result

    def delete(self, name):
        """Delete storage file.
        Args:
            name: relative file name
        Raises:
            StorageException
        """
        try:
            location = self._name_to_location(name)
            self.container.delete_object(location)
        except Exception as error:
            logging.exception(error)
            raise exception.FileOperationFailed(str(error))


class CloudfilesStoragePool(QueuePool):
    """Cloudfiles storage pool.

    CloudfilesStorage is not thread / greenlet safe. This class provides a mechanism
    for pooling CloudfilesStorage objects in a thread / greenlet safe manner.
    
    Example usage:
        with pool.get() as storage:
            storage.listdir()
    """
    
    def __init__(self,
            cloudfiles_connection_factory,
            container_name,
            size,
            location_base=None,
            queue_class=Queue.Queue):

        """RiakSessionStorePool constructor.

        Args:
            cloudfiles_connection_factory: Factory object to create
                cloudfiles.Connection objects.
            container_name: cloud files container name
            size: Number of RiakSessionStore objects to include in pool.
            location_base: optional location within the container
                where files should be stored. Note that the
                location_base will not be exposed to applications,
                for example, in the relative filename returned
                save().
            queue_class: Optional Queue class. If not provided, will
                default to Queue.Queue. The specified class must
                have a no-arg constructor and provide a get(block, timeout)
                method.
        """
        self.cloudfiles_connection_factory = cloudfiles_connection_factory
        self.container_name = container_name
        self.size = size
        self.location_base = location_base
        self.queue_class = queue_class
        super(CloudfilesStoragePool, self).__init__(
                self.size,
                factory=self,
                queue_class=self.queue_class)
    
    def create(self):
        """CloudfilesStorage factory method."""
        connection = self.cloudfiles_connection_factory.create()
        return CloudfilesStorage(
                connection=connection,
                container_name=self.container_name,
                location_base=self.location_base)
