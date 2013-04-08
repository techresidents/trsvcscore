import abc
import uuid
import time

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
    def user_id(self):
        """Get user id associated with session.

        Returns:
            User id if session is authenticated, None otherwise.
        """
        return

    @abc.abstractmethod
    def tenant_id(self):
        """Get tenant id associated with session.

        Returns:
            Tenant id if session is authenticated, None otherwise.
        """
        return

    @abc.abstractmethod
    def expires(self):
        """Get session expiration time.

        Returns:
            Expiration time in seconds (Epoch time)
        """
        return

    @abc.abstractmethod
    def is_authenticated(self):
        """Test if session is authenticated (user_id present).

        Returns:
            True if session is authenticated, False otherwise.
        """
        return self.user_id() is not None

    @abc.abstractmethod
    def is_expired(self):
        """Test if session is expired.

        Returns:
            True if session is expired, False otherwise.
        """
        return time.time() >= self.expires()


class SessionStore(object):
    """Session store base class."""
    __metaclass__ = abc.ABCMeta
    
    #Default session length to one day
    DEFAULT_SESSION_LIFE = 86400

    def _create_session_key(self):
        return uuid.uuid4().hex

    @abc.abstractmethod
    def create(self, expire_time=None, user_id=None, session_key=None):
        """Create a new session.

        Args:
            expire_time: Optional expirate time in seconds (Epoch time)
                when the session should expire. If None, the current
                time + DEFAULT_SESSION_LIFE will be used.
            user_id: Optional user_id to determine authentication status.
            session_key: optional session key to use. If provided
                the session_key must be unique or SessionException
                will be raised. If not provided, a unique session key
                will be created.
        
        Returns:
            Session object 
        """
        return
    
    @abc.abstractmethod
    def get_session(self, session_key, allow_expired=False, allow_non_authenticated=False):
        """Get a session for the give session_key with specified allowances.

        Args:
            session_key: session key (string)       
            allow_expired: allow expired sessions to be returned.
            allow_non_authenticated: allow non-authenticated sessions
                to be returned.
        Returns:
            Session object if session is found and non-expired,
            None otherwise.
        """
        return
