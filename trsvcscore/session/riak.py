import time

from trsvcscore.session.base import Session, SessionStore, SessionException


class RiakSession(Session):
    def __init__(self, session):
        """Session constructor.

        Args:
            session_key: unique session key (string)
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
    
    def expires(self):
        """Get session expiration time.

        Returns:
            Expiration time in seconds (Epoch time)
        """
        data = self._session.get_data()
        return data.get("expire_time", None)
        

class RiakSessionStore(SessionStore):

    def __init__(self, client, bucket_name):
        """RiakSessionStore constructor.

        Args:
            client: Riak client object
            bucket_name: Riak session bucket name (string)
        """
        self.client = client
        self.bucket = self.client.bucket(bucket_name)

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
                "expire_time" : expire_time
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
    
    def get_session(self, session_key):
        """Get a session for the give session_key.

        Args:
            session_key: session key (string)       
        Returns:
            RiakSession object if session if found and valid,
            None otherwise.
        """
        if session_key is None:
            return None

        session = self.bucket.get(session_key)

        #If the session exists and is not expired, return it.
        if session.exists() and time.time() < session.get_data()["expire_time"]:
            return RiakSession(session)
        else:
            return None
