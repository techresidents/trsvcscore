import thrift
from thrift.transport.TTransport import TTransportException

from trpycore.pool.queue import QueuePool
from trsvcscore.proxy.base import ServiceProxyException, ServiceProxy

class BasicServiceProxy(ServiceProxy):
    """Basic service proxy.

    This class provides a convenience proxy for consuming
    services in a robust manner, properly handling
    service disconnections.

    This class will proxy all methods and attributes to the
    underlying service object. If the service is unavailable,
    a ServiceProxyException will be raised.

    Example usage:
        proxy = BasicServiceProxy("chatsvc", "localhost", 9090)
        proxy.getVersion(RequestContext())
    """


    def __init__(self, service_name, service_hostname, service_port,
            service_class=None, transport_class=None,
            protocol_class=None, keepalive=False, is_gevent=False):
        """BasicServiceProxy constructor.

        Args:
            service_name: Service name, i.e., chatsvc
            service_hostname: service hostname
            service_port: service port
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
        super(BasicServiceProxy, self).__init__(
                service_name,
                service_class,
                transport_class,
                protocol_class,
                keepalive,
                is_gevent)

        self.service_hostname = service_hostname
        self.service_port = service_port
        self.is_gevent = is_gevent

        self.service_transport = self.transport_class(self.service_hostname, self.service_port)
        self.service_protocol = self.protocol_class(self.service_transport)
        self.service = self.service_class.Client(self.service_protocol)

        self.service_method_wrappers  ={}


    def open_transport(self):
        """Open service transport.
        Raises:
            ServiceProxyException if service is not available.
        """
        try:
            if self.service_transport:
                if not self.service_transpot.isOpen():
                    self.service_transport.open()
            else:
                raise ServiceProxyException("service unavailable")
        except Exception:
            raise ServiceProxyException("service unavailable")
    
    def close_transport(self):
        """Open service transport.
        Raises:
            ServiceProxyException if service is not available.
        """
        try:
            if self.service_transport:
                if self.service_transpot.isOpen():
                    self.service_transport.close()
            else:
                raise ServiceProxyException("service unavailable")
        except Exception:
            raise ServiceProxyException("service unavailable")

        
    def _get_service_method_wrapper(self, method):
        """Create a service method wrapper to manage transport.

        Users will receive a wrapper version of service methods
        which ensures that the transport is opened for each
        request and is properly governed by keepalive setting.
        """

        if method not in self.service_method_wrappers:
            def wrapper(*args, **kwargs):
                try:
                    if not self.service_transport.isOpen():
                        self.service_transport.open()
                    return method(*args, **kwargs)
                except TTransportException as error:
                    self.service_transport.close()
                    raise ServiceProxyException("service unavailable: %s" % str(error))
                finally:
                    if not self.keepalive and self.service_transport.isOpen():
                        self.service_transport.close()
            self.service_method_wrappers[method] = wrapper
        return self.service_method_wrappers[method]


    def __getattr__(self, attr):
        """Proxy all attributes to service object.

        This method will proxy all attribute requests
        to the underlying service object. This allow users
        to invoke service methods directly through
        this class. 

        Note that service methods will be decorated with a
        wrapper which ensures that the transport is open
        and governed per the keepalive setting.

        Raises:
            ServiceProxyException if service is not available.
        """

        #If the service is unavailable raise ServiceProxyException.
        if self.service is None:
            raise ServiceProxyException("service unavailable")
        
        #Return service object attribute.
        attribute = getattr(self.service, attr)
        if hasattr(attribute, "__call__"):
            attribute = self._get_service_method_wrapper(attribute)
        return attribute


class BasicServiceProxyPool(QueuePool):
    """Basic service proxy pool.
    
    Creates a queue of BasicServiceProxy objects for use across threads / greenlets
    depending on the chosen queue_class.

    Example usage:
        with pool.get() as service:
            service.getVersion(RequestContext())
    """
    
    def __init__(self, service_name, service_hostname, service_port, size,
            service_class=None, queue_class=None,
            transport_class=None, protocol_class=None,
            keepalive=False, is_gevent=False):
        """BasicServiceProxyPool constructor.

        Args:
            service_name: Service name, i.e. chatsvc
            service_hostname: Service hostname
            service_port: Service port
            service_class: Optional service class, i.e. TChatService.
                If not provided, TRService will be used which will
                only provide proxying to the service methods defined
                within TRService.
            size: Number of ZookeeperSessionStore objects to include in pool.
            queue_class: Optional queue class. If not provided, will
                default to Queue.Queue or gevent.queue.Queue depending
                on the value of is_gevent. The specified class must
                have a no-arg constructor and provide a get(block, timeout)
                method.
            transport_class: Optional Thrift transport class. If not
                provided TSocket will be used. TSocket will be
                appropriately patched for gevent comptability
                if is_gevent is set to True.
                appropriately patched for gevent comptability.
            protocol_class: Option Thrift protocol class. If not
                provided this will default to TBinaryProtocol.
            keepalive: Optional boolean indicating if transport should
                be kept open between requests. If false, transport
                will be opened and closed for each service request.
            is_gevent: Optional boolean indicating if this is a 
                gevent based service. If so, the default TSocket
                transport_class will be patched for gevent 
                compatability, and an appropriate queue class will
                be used.
        """
        self.service_name = service_name
        self.service_hostname = service_hostname
        self.service_port = service_port
        self.size = size
        self.service_class = service_class
        self.queue_class = queue_class
        self.transport_class = transport_class
        self.protocol_class = protocol_class
        self.keepalive = keepalive
        self.is_gevent = is_gevent

        if self.queue_class is None:
            if self.is_gevent:
                import gevent.queue
                self.queue_class = gevent.queue.Queue
            else:
                import Queue
                self.queue_class = Queue.Queue
        super(BasicServiceProxyPool, self).__init__(
                self.size,
                factory=self,
                queue_class=self.queue_class)
    
    def create(self):
        """BasicServiceProxy factory method."""
        return BasicServiceProxy(
                self.service_name,
                self.service_hostname,
                self.service_port,
                service_class=self.service_class,
                transport_class=self.transport_class,
                protocol_class=self.protocol_class,
                keepalive=self.keepalive,
                is_gevent=self.is_gevent)
