class StorageException(Exception):
    """Base storage exception."""
    pass

class FileDoesNotExist(StorageException):
    """File does not exist exception."""
    pass

class FileNotOpen(StorageException):
    """File not open exception."""
    pass

class FileOperationNotAllowed(StorageException):
    """File operation not allowed exception."""
    pass

class FileOperationFailed(StorageException):
    """File operation failed exception."""
    pass

class NotImplemented(StorageException):
    """Not implemented exception."""
    pass

class InvalidArgument(StorageException):
    """Invalid argument exception."""
    pass

