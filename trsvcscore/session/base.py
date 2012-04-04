import abc
import uuid

class SessionException(Exception):
    pass

class Session(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, session_key):
        self._session_key = session_key
    
    @abc.abstractmethod
    def get_key(self):
        return self._session_key

    @abc.abstractmethod
    def get_data(self):
        return

    @abc.abstractmethod
    def set_data(self, data):
        return

    @abc.abstractmethod
    def save(self):
        return

    @abc.abstractmethod
    def delete(self):
        return

    @abc.abstractmethod
    def expires(self):
        return


class SessionStore(object):
    __metaclass__ = abc.ABCMeta
    
    #Default session length to one day
    DEFAULT_SESSION_LIFE = 86400

    def _create_session_key(self):
        return uuid.uuid4().hex

    @abc.abstractmethod
    def create(self, expire_time=None, session_key=None):
        return
    
    @abc.abstractmethod
    def get_session(self, session_key):
        return
