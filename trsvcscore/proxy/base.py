import abc

from thrift.protocol import TBinaryProtocol

from tridlcore.gen import TRService

class ServiceProxyException(Exception):
    """General service proxy exception class."""
    pass

class ServiceProxy(object):
    """Service proxy abstract base class.

    Service proxies provides a convenience mechanism for consuming
    services in a robust manner, properly handling service
    disconnections.

    Service proxies proxy all methods and attributes to the
    underlying service object. If the service is unavailable,
    a ServiceProxyException will be raised.

    Example usage:
        proxy = ZookeeperServiceProxy(client, "chatsvc")
        proxy.getVersion(RequestContext())
    """
    __metaclass__ = abc.ABCMeta


    def __init__(self, service_name, service_class=None,
            transport_class=None, protocol_class=None,
            keepalive=False, is_gevent=False):
        """ServiceProxy constructor.

        Args:
            service_name: Service name, i.e., chatsvc
            service_class: Optional service class, i.e. TChatService.
                If not provided, TRService will be used which will
                only provide proxying to the service methods defined
                within TRService.
            transport_class: Optional Thrift transport class. If not
                provided TSocket will be used. TSocket will be
                appropriately patched for gevent comptability
                if is_gevent is set to True.
            protocol_class: Option Thrift protocol class. If not
                provided this will default to TBinaryProtocol.
            keepalive: Optional boolean indicating if transport should
                be kept open between requests. If false, transport
                will be opened and closed for each service request.
            is_gevent: Optional boolean indicating if this is a 
                gevent based service. If so, the default TSocket
                transport_class will be patched for gevent 
                compatability.
        """
        self.service_name = service_name
        self.keepalive = keepalive
        self.is_gevent = is_gevent
        self.service_class = service_class or TRService
        self.protocol_class = protocol_class or TBinaryProtocol.TBinaryProtocol

        #If in a gevent app and adjust the transport accordingly
        if self.is_gevent:
            from trpycore.thrift_gevent.transport import TSocket
            self.transport_class = transport_class or TSocket.TSocket
        else:
            from thrift.transport import TSocket
            self.transport_class = transport_class or TSocket.TSocket
    
    @abc.abstractmethod
    def open_transport(self):
        """Open service transport.
        Raises:
            ServiceProxyException if service is not available.
        """
        return
    
    @abc.abstractmethod
    def close_transport(self):
        return
