import datetime
import errno
import os
import StringIO

from trsvcscore.storage.base import StorageFile, Storage
from trsvcscore.storage import exception

class FileSystemStorageFile(StorageFile):
    """File system storage file.

    StorageFile objects should not typically be instantiated directly. Instead
    the Storage object backend should be used in order to obtain a StorageFile
    object.
    
    All StorageFile names are relative. For example,
    'me.jpeg', or 'photos/me.jpeg' are okay, but not '/mypath/photos/me.jpeg'.
    This is intentional so that the names can be persisted if needed,
    and still allow for Storage backends to be switched without too
    much trouble.
    """
    
    def __init__(self, location, name, mode):
        """FileSystemStorageFile constructor.

        Args:
            location: absolute path to working directory
            name: name relative to the specified location
            mode: file mode, i.e. 'rb'
        """
        super(FileSystemStorageFile, self).__init__(name, mode)
        self.location = location
        self.path = os.path.join(location, name)
        self.file = None

        self.open(mode)
    
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
        return os.path.getsize(self.path)

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
        self._mode = mode or self._mode
        
        if self.file:
            self.close()
        try:
            self.file = open(self.path, self._mode)
        except Exception as error:
            raise exception.FileOperationFailed(str(error))

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
        if self.file:
            try:
                size = size or self.size()
                return self.file.read(size)
            except Exception as error:
                raise exception.FileOperationFailed(str(error))
        else:
            raise exception.FileNotOpen("file not open")

    def write(self, data):
        """Write data to file.

        Args:
            data: string of file like object containing
                  a read(n) method.
        Raises:
            StorageException
        """
        if self.file:
            try:
                if isinstance(data, basestring):
                    self.file.write(data)
                elif hasattr(data, "read"):
                    while True:
                        chunk = data.read(4096)
                        if chunk:
                            self.file.write(chunk)
                        else:
                            break
                else:
                    raise RuntimeError("invalid data argument")
            except Exception as error:
                raise exception.FileOperationFailed(str(error))
        else:
            raise exception.FileNotOpen("file not open")
    
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
        if self.file:
            try:
                self.file.seek(offset, whence)
            except Exception as error:
                raise exception.FileOperationFailed(str(error))
        else:
            raise exception.FileNotOpen("file not open")
    
    def tell(self):
        """Return file pointer offset.

        Returns:
            file pointer offset.
        Raises:
            StorageException
        """
        if self.file:
            return self.file.tell()
        else:
            raise exception.FileNotOpen("file not open")

    def close(self):
        """Close the file."""
        if self.file:
            self.file.close()
            self.file = None


class FileSystemStorage(Storage):
    """File system storage backend.

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
    
    def __init__(self, location):
        """FileSystemStorage constructor.

        Args:
            location: absolute path to working directory.
                All relative names will be resolved 
                relative to this path.
        """
        self.location = location
        if not os.path.exists(location):
            os.makedirs(location)

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
        path = self.path(path or "")

        for entry in os.listdir(path):
            if os.path.isdir(os.path.join(path, entry)):
                directories.append(entry)
            else:
                files.append(entry)
        
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
        return os.path.exists(self.path(name))

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
            path = self.path(name)
            return datetime.datetime.utcfromtimestamp(os.path.getmtime(path))
        except Exception as error:
            raise exception.FileOperationFailed(str(error))

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
        return FileSystemStorageFile(self.location, name, mode)

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
        path = self.path(name)
        directory = os.path.dirname(path)
        
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except OSError as error:
                if error.errno != errno.EEXIST:
                    raise exception.FileOperationFailed(str(error))
            except Exception as error:
                raise exception.FileOperationFailed(str(error))

        if os.path.exists(path):
            raise exception.FileOperationFailed("'%s' already exists" % name)

        with FileSystemStorageFile(self.location, name, "w") as storage_file:
                storage_file.write(data)
        
    def size(self, name):
        """Get storage file size.

        Args:
            name: relative filename
        Returns:
            file size in bytes.
        Raises:
            StorageException
        """
        return os.path.getsize(self.path(name))
    
    def path(self, name):
        """Get local filesystem path of storage file.

        Args:
            name: relative filename
        Returns:
            local filesystem path to file.
        Raises:
            StorageException
        """
        return os.path.join(self.location, name)

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
        raise exception.NotImplemented()

    def delete(self, name):
        """Delete storage file.
        Args:
            name: relative file name
        Raises:
            StorageException
        """
        os.remove(self.path(name))
