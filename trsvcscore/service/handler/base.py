import abc

class Handler(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def start(self):
        return

    @abc.abstractmethod
    def stop(self):
        return

    @abc.abstractmethod
    def join(self, timeout=None):
        return
