import logging
import os
import threading

from trpycore.pool.queue import QueuePool
from trpycore.zookeeper_gevent.watch import GChildrenWatch
from trpycore.zookeeper.watch import ChildrenWatch
from trsvcscore.registrar.zookeeper import ZookeeperServiceRegistrar
from trsvcscore.proxy.base import ServiceProxyException, ServiceProxy
from trsvcscore.service.server.base import ServerProtocol, ServerTransport

class ZookeeperServiceProxy(ServiceProxy):
    """Zookeeper based service proxy.

    This class provides a convenience proxy for consuming
    services in a robust manner which automatically handles
    locating service instances on the network and adjusting
    for service unavailability.

    This class assumes that all available services will have
    registered with ZookeeperServiceRegistrar.

    This class will proxy all methods and attributes to the
    underlying service object. If no service is unavailable,
    a ServiceProxyException will be raised.

    Example usage:
        proxy = ZookeeperServiceProxy(client, "chatsvc")
        proxy.getVersion(RequestContext())
    """

    class NoOpLock(object):
        """Lock context manager which does nothing, no-op.

        This is a standin for a lock context manager, when
        locking is not really needed.
        """
        def __enter__(self):
            return

        def __exit__(self, exception_type, exception_value, exception_traceback):
            """Exit context manager without supressing exceptions."""
            return False


    def __init__(self, zookeeper_client, service_name,
            service_class=None, transport_class=None, protocol_class=None,
            keepalive=False, is_gevent=False):
        """ZookeeperServiceProxy constructor.

        Args:
            zookeeper_client: Zookeeper client object.  Implementation
                of this proxy will be adjusted based on if this is a
                ZookeeperClient or GZookeeperClient instance.
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
        super(ZookeeperServiceProxy, self).__init__(
                service_name,
                service_class,
                transport_class,
                protocol_class,
                keepalive,
                is_gevent)

        self.zookeeper_client = zookeeper_client
        self.registrar = ZookeeperServiceRegistrar(self.zookeeper_client)
        self.registry_path = os.path.join("/services", self.service_name, "registry")

        self.service = None               #Service client object
        self.service_transport = None     #Service client transport
        self.service_node = None          #Service zookeeper node, i.e. chatsvc_00000001
        self.service_method_wrappers = {} #Service method wrappers
        
        #Staged service client object, node, and transport.
        #If the the current self.service become unavailable
        #the _watcher() callback will be invoked asynchronously
        #by the zookeeper client. At this point, we'll create
        #a new service client object and stage it for update
        #on the next user invocation.
        self.staged_service = None
        self.staged_service_node = None
        self.staged_service_transport = None
        
        #If we're in a gevent app adjust the lock, and watch accordingly.
        if self.is_gevent:
            self.watch = GChildrenWatch(self.zookeeper_client, self.registry_path, self._watch)
            self.lock = self.NoOpLock()
        else:
            self.watch = ChildrenWatch(self.zookeeper_client, self.registry_path, self._watch)
            self.lock = threading.Lock()
        
        #Acquire the lock, and create the service client.
        with self.lock:
            self.service_node, self.service, self.service_transport = self._create_service()

        #Start watching zookeeper /services/<service_name>/registry for
        #addition and removal of service instances, so we can
        #update our proxy if our instance goes down.
        self.watch.start()

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

    def _watch(self, watcher):
        """Zookeper watcher callback.

        This method will be invoked asynchronously if instances
        of this service are added or removed. If our instance
        is no longer available, create a new, staged, service
        object while will be swapped in on the next user
        invocation.
        """
        services = watcher.get_children()

        #If our service is no longer available, create a new one.
        if self.service_node not in services and \
            self.staged_service_node not in services:
            
            node, service, transport = self._create_service()
            
            #Update staged service and node.
            with self.lock:
                self.staged_service_node = node
                self.staged_service = service
                self.staged_service_transport = transport
        
    def _create_service(self):
        """Create a new service client object.

        Returns:
            (Zookeeper node, Service, Transport) tuple if service is available,
            otherwise (None, None, None).
        """
        result = (None, None, None)
        
        #Locate an available service instance in the registrar
        path, service_info = self.registrar.locate_zookeeper_service(self.service_name)

        #If a service instance is available, create the object and stage
        #it to be swapped in on the next user invocation.
        if path and service_info:
            for server in service_info.servers:
                for endpoint in server.endpoints:
                    if endpoint.protocol ==  ServerProtocol.THRIFT and \
                            endpoint.transport == ServerTransport.TCP:
                        node = os.path.basename(path)
                        transport = self.transport_class(endpoint.address, endpoint.port)
                        protocol = self.protocol_class(transport)
                        service = self.service_class.Client(protocol)

                        result = (node, service, transport)
                        return result
        return result

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
                except Exception as error:
                    logging.exception(error)
                    raise ServiceProxyException("service unavailable")
                finally:
                    if not self.keepalive and self.service_transport.isOpen():
                        self.service_transport.close()
            self.service_method_wrappers[method] = wrapper
        return self.service_method_wrappers[method]


    def __getattr__(self, attr):
        """Proxy all attributes to service object.

        This method will proxy all attribute requests
        to the underlying service object. This allow users
        to invoke service methods directrly through
        this class. 

        Note that service methods will be decorated with a
        wrapper which ensures that the transport is open
        and governed per the keepalive setting.

        Raises:
            ServiceProxyException if service is not available.
        """

        #If a new service object is stage, acquire the
        #lock and swap it in.
        if self.staged_service:
            with self.lock:
                self.service = self.staged_service
                self.staged_service = None

                self.service_node = self.staged_service_node
                self.staged_service_node = None

                self.service_transport = self.staged_service_transport
                self.staged_service_transport = None
        
        #If the service is unavailable raise ServiceProxyException.
        if self.service is None:
            raise ServiceProxyException("service unavailable")
        
        #Return service object attribute.
        attribute = getattr(self.service, attr)
        if hasattr(attribute, "__call__"):
            attribute = self._get_service_method_wrapper(attribute)
        return attribute


class ZookeeperServiceProxyPool(QueuePool):
    """Zookeeper service proxy pool.
    
    Creates a queue of ZookeeperServiceProxy objects for use across threads / greenlets.

    Example usage:
        with pool.get() as service:
            service.getVersion(RequestContext())
    """
    
    def __init__(self, zookeeper_client, service_name, size,
            service_class=None, queue_class=None,
            transport_class=None, protocol_class=None,
            keepalive=False, is_gevent=False):
        """ZookeeperServiceProxyPool constructor.

        Args:
            zookeeper_client: Zookeeper client object.
            service_name: Service name, i.e. chatsvc
            size: Number of ZookeeperSessionStore objects to include in pool.
            service_class: Optional service class, i.e. TChatService.
                If not provided, TRService will be used which will
                only provide proxying to the service methods defined
                within TRService.
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
        self.zookeeper_client = zookeeper_client
        self.service_name = service_name
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

        super(ZookeeperServiceProxyPool, self).__init__(
                self.size,
                factory=self,
                queue_class=self.queue_class)
    
    def create(self):
        """ZookeeperServiceProxy factory method."""
        return ZookeeperServiceProxy(
                self.zookeeper_client,
                self.service_name,
                service_class=self.service_class,
                transport_class=self.transport_class,
                protocol_class=self.protocol_class,
                keepalive=self.keepalive,
                is_gevent=self.is_gevent)
