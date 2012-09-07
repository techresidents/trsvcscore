import abc

from trsvcscore.storage.exception import InvalidArgument


class StorageFile(object):
    """Abstract base class representing a file located on a storage backend.
        
    StorageFile objects should not typically be instantiated directly. Instead
    the Storage object backend should be used in order to obtain a StorageFile
    object.
    
    All StorageFile names are relative. For example,
    'me.jpeg', or 'photos/me.jpeg' are okay, but not '/mypath/photos/me.jpeg'.
    This is intentional so that the names can be persisted if needed,
    and still allow for Storage backends to be switched without too
    much trouble.
    """
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, name, mode):
        """StorageFile constructor.

        Args:
            name: relative name, i.e. 'me.jpeg' or 'photos/me.jpeg'
            mode: file mode, i.e. 'rb'
        Raises:
            StorageException
        """
        self._name = name
        self._mode = mode
    
    def __enter__(self):
        """Context manager enter.

        Returns:
            StorageFile object
        """
        return self

    def __exit__(self, exc_type, exc_value, tb):
        """Context manager exit which closes the file.
        """
        self.close()
    
    def __len__(self):
        """Length of file.

        Returns:
            size of file in bytes.
        """
        return self.size()

    @abc.abstractmethod
    def name(self):
        """Get relative file name.

        Returns:
            relative filename, i.e. 'photos/me.jpeg'
        """
        return self._name

    @abc.abstractmethod
    def mode(self):
        """Get file mode.

        Returns:
            file mode, i.e. 'rb'
        """
        return self._mode

    @abc.abstractmethod
    def size(self):
        """Get file size.

        Returns:
            file size in bytes.
        Raises:
            StorageException
        """
        return

    @abc.abstractmethod
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
        return

    @abc.abstractmethod
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
        return

    @abc.abstractmethod
    def write(self, data):
        """Write data to file.

        Args:
            data: string of file like object containing
                  a read(n) method.
        Raises:
            StorageException
        """
        return

    @abc.abstractmethod
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
        return

    @abc.abstractmethod
    def tell(self):
        """Return file pointer offset.

        Returns:
            file pointer offset.
        Raises:
            StorageException
        """
        return

    @abc.abstractmethod
    def close(self):
        """Close the file."""
        return


class Storage(object):
    """Abstract storage base class representing a storage backend.
    
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
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def listdir(self, path=None):
        """Get directory,file listing.

        Args:
            path: optional relative path to filter.
        Returns:
            (list_of_directories, list_of_files) tuple
        Raises:
            StorageException
        """
        return

    @abc.abstractmethod
    def exists(self, name):
        """Check if storage file exists.

        Args:
            name: relative filename
        Returns:
            boolean indicating if storage file exists.
        Raises:
            StorageException
        """
        return

    @abc.abstractmethod
    def modified_time(self, name):
        """File modification utc datetime object.

        Args:
            name: relative filename
        Returns:
            file modification utc datetime object.
        Raises:
            StorageException
        """
        return

    @abc.abstractmethod
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
        return

    @abc.abstractmethod
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
        return

    @abc.abstractmethod
    def size(self, name):
        """Get storage file size.

        Args:
            name: relative filename
        Returns:
            file size in bytes.
        Raises:
            StorageException
        """
        return

    @abc.abstractmethod
    def path(self, name):
        """Get local filesystem path of storage file.

        Args:
            name: relative filename
        Returns:
            local filesystem path to file.
        Raises:
            StorageException
        """
        return

    @abc.abstractmethod
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
        return

    @abc.abstractmethod
    def delete(self, name):
        """Delete storage file.
        Args:
            name: relative file name
        Raises:
            StorageException
        """
        return


class StorageFileMode(object):
    """Class representation for file modes.
    
    This class provides a mechanism for parsing file modes.

    File modes:
        r  : read-only mode. File pointer placed at beginning of file.
        r+ : read-write mode. File pointer placed at begninning of file.
        w  : write-only mode. Overwrite file if the file exists. If the file
             does not exist, create a new file for writing.
        w+ : read-write mode. Overwrite file if the file exists. If the file 
             does not exit, create a new file for reading and writing.
        a  : write-only mode. The file pointer is placed at the end of the file 
             if the file exists. If the file does not exist, create a new
             file for writing.
        a+ : read-write mode. The file pointer is placed at the end of the file
             if the file exists (append mode). If the file does not exist,
             create a new file for reading and writing.

    Option file mode qualifiers:
        b  : binary file
        t  : text file
    """

    def __init__(self, mode):
        """StorageFileMode constructor.
        
        Args:
            mode: file mode, i.e. 'r+'
        Raises:
            StorageException
        """
        self.mode = mode
        
        #modes
        self.readable = False
        self.writable = False
        self.append = False
        self.plus = False
        self.binary = False
        self.text = False

        #flags
        self.create = False
        self.truncate = False

        self._parse(mode)
    
    def _parse(self, mode):
        mode_set = False

        for c in mode:
            if c == "r":
                if mode_set:
                    raise InvalidArgument("invalid mode")
                self.readable = True
                mode_set = True
            elif c == "w":
                if mode_set:
                    raise InvalidArgument("invalid mode")
                self.writable = self.create = self.truncate = True
                mode_set = True
            elif c == "a":
                if mode_set:
                    raise InvalidArgument("invalid mode")
                self.writable = self.append = self.create = True
                mode_set = True
            elif c == "b":
                self.binary = True
            elif c == "t":
                self.text = True
            elif c == "+":
                self.readable = self.writable = True
            else:
                raise InvalidArgument("invalid mode")
