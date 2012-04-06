import abc
import uuid

class SessionException(Exception):
    """General purpose session exception."""
    pass

class Session(object):
    """Abstract session base class to represent a session."""
    __metaclass__ = abc.ABCMeta

    def __init__(self, session_key):
        """Session constructor.

        Args:
            session_key: unique session key (string)
        """
        self._session_key = session_key
    
    @abc.abstractmethod
    def get_key(self):
        """Get unique session key.

        Returns:
            Unique session key (string)
        """
        return self._session_key

    @abc.abstractmethod
    def get_data(self):
        """Get session data.

        Returns:
            Dict of key / value session data (string)
        """
        return

    @abc.abstractmethod
    def set_data(self, data):
        """Set session data.

        Args:
            data: Dict of key / value session data (string)
        """
        return

    @abc.abstractmethod
    def save(self):
        """Save updated seession data to session store."""
        return

    @abc.abstractmethod
    def delete(self):
        """Delete this session from session store."""
        return

    @abc.abstractmethod
    def expires(self):
        """Get session expiration time.

        Returns:
            Expiration time in seconds (Epoch time)
        """
        return


class SessionStore(object):
    """Session store base class."""
    __metaclass__ = abc.ABCMeta
    
    #Default session length to one day
    DEFAULT_SESSION_LIFE = 86400

    def _create_session_key(self):
        return uuid.uuid4().hex

    @abc.abstractmethod
    def create(self, expire_time=None, session_key=None):
        """Create a new session.

        Args:
            expire_time: Optional expirate time in seconds (Epoch time)
                when the session should expire. If None, the current
                time + DEFAULT_SESSION_LIFE will be used.
            session_key: optional session key to use. If provided
                the session_key must be unique or SessionException
                will be raised. If not provided, a unique session key
                will be created.
        
        Returns:
            Session object 
        """
        return
    
    @abc.abstractmethod
    def get_session(self, session_key):
        """Get a session for the give session_key.

        Args:
            session_key: session key (string)       
        Returns:
            Session object if session if found and valid,
            None otherwise.
        """
        return
