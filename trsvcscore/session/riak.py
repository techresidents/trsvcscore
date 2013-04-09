import Queue
import time

from trpycore.pool.queue import QueuePool
from trsvcscore.session.base import Session, SessionStore, SessionException


class RiakSession(Session):
    def __init__(self, session):
        """Session constructor.

        Args:
            session: Riak session bucket object.
        """
        super(RiakSession, self).__init__(session.get_key())
        self._session = session
    
    def get_key(self):
        """Get unique session key.

        Returns:
            Unique session key (string)
        """
        return super(RiakSession, self).get_key()
    
    def get_data(self):
        """Get session data.

        Returns:
            Dict of key / value session data (string)
        """
        data = self._session.get_data()
        return data.get("session_data", {})
    
    def set_data(self, data):
        """Set session data.

        Args:
            data: Dict of key / value session data (string)
        """
        data = self._session.get_data()
        data["session_data"] = data
        self._session.set_data(data)
    
    def save(self):
        """Save updated seession data to session store."""
        self._session.store()
    
    def delete(self):
        """Delete this session from session store."""
        self._session.delete()

    def user_id(self):
        """Get user id associated with session.

        Returns:
            User id if session is authenticated, None otherwise.
        """
        data = self._session.get_data()
        return data.get("user_id", None)

    def tenant_id(self):
        """Get tenant id associated with session.

        Returns:
            Tenant id if session is authenticated, None otherwise.
        """
        data = self._session.get_data()
        return data.get("tenant_id", None)
    
    def expires(self):
        """Get session expiration time.

        Returns:
            Expiration time in seconds (Epoch time)
        """
        data = self._session.get_data()
        return data.get("expire_time", None)

    def is_authenticated(self):
        """Test if session is authenticated (user_id present).

        Returns:
            True if session is authenticated, False otherwise.
        """
        return super(RiakSession, self).is_authenticated()

    def is_expired(self):
        """Test if session is expired.

        Returns:
            True if session is expired, False otherwise.
        """
        return super(RiakSession, self).is_expired()
        

class RiakSessionStore(SessionStore):

    def __init__(self, client, bucket_name):
        """RiakSessionStore constructor.

        Args:
            client: Riak client object
            bucket_name: Riak session bucket name (string)
        """
        self.client = client
        self.bucket = self.client.bucket(bucket_name)

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
            RiakSession object 
        """
        expire_time = expire_time or time.time() + SessionStore.DEFAULT_SESSION_LIFE
        session_key_provided = session_key is not None

        while True:
            session_key = session_key or self._create_session_key()
            session = self.bucket.get(session_key)

            if session.exists():
                if session_key_provided:
                    raise SessionException
                else:
                    continue
            
            data = {
                "session_data" : {},
                "expire_time" : expire_time,
                "user_id": user_id,
            }
            
            
            session.set_data(data)
            
            #Store the session with if_none_match set to True.
            #This will result in an "Exception" if object already exists.
            #This is extremely to happen since we also check if the object
            #exists at the start of the loop.
            try:
                session.store(if_none_match=True)
            except Exception:
                if session_key_provided:
                    raise SessionException
                else:
                    continue

            return RiakSession(session)
    
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
        if session_key is None:
            return None

        session = self.bucket.get(session_key)

        if session.exists():
            riak_session = RiakSession(session)
            if (allow_expired or not riak_session.is_expired()) \
                    and (allow_non_authenticated or riak_session.is_authenticated()):
                return riak_session
        else:
            return None


class RiakSessionStorePool(QueuePool):
    """Riak session store pool.

    RiakClient is not thread / greenlet safe. This class provides a mechanism
    for pooling RiakSessionStore objects in a thread / greenlet safe manner.
    
    Example usage:
        with pool.get() as session_store:
            session_store.create()
    """
    
    def __init__(self, riak_client_factory, bucket_name, size, queue_class=Queue.Queue):
        """RiakSessionStorePool constructor.

        Args:
            riak_client_factory: Factory object to create RiakClient objects.
            bucket_name: Riak session bucket name.
            size: Number of RiakSessionStore objects to include in pool.
            queue_class: Optional Queue class. If not provided, will
                default to Queue.Queue. The specified class must
                have a no-arg constructor and provide a get(block, timeout)
                method.
        """
        self.riak_client_factory = riak_client_factory
        self.bucket_name = bucket_name
        self.size = size
        self.queue_class = queue_class
        super(RiakSessionStorePool, self).__init__(
                self.size,
                factory=self,
                queue_class=self.queue_class)
    
    def create(self):
        """RiakSessionStore factory method."""
        riak_client = self.riak_client_factory.create()
        return RiakSessionStore(riak_client, self.bucket_name)
