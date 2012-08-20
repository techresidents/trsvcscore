import abc

class Handler(object):
    """Handler abstract base class.

    Services consist of one or more servers, which expose portions of the
    service interface through one or more endpoints. Each server fulfills
    the service interface through delegation to its Handler's.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def start(self):
        """Start handler."""
        return

    @abc.abstractmethod
    def stop(self):
        """Stop handler."""
        return

    @abc.abstractmethod
    def join(self, timeout=None):
        """Join the handler.

        Join the handler, waiting for the completion of all threads 
        or greenlets.

        Args:
            timeout: Optional timeout in seconds to observe before returning.
                If timeout is specified, the status() method must be called
                to determine if the handler is still running.
        """
        return

    @abc.abstractmethod
    def status(self):
        """Get the handler status.

        Returns Status enum.
        """
        return
