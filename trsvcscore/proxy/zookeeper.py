import logging
import os
import Queue
import threading

from thrift.protocol import TBinaryProtocol

from tridlcore.gen import TRService
from trpycore.pool.queue import QueuePool
from trpycore.zookeeper_gevent.client import GZookeeperClient
from trpycore.zookeeper_gevent.watch import GChildrenWatch
from trpycore.zookeeper.watch import ChildrenWatch
from trsvcscore.registrar.zookeeper import ZookeeperServiceRegistrar
from trsvcscore.proxy.base import ServiceProxyException

class ZookeeperServiceProxy(object):
    """Zookeeper based service proxy.

    This class provides a convenience proxy for consuming
    services in a robust manner which automatically handles
    locating service instances on the network and adjusting
    for service unavailability.

    This class assumes that all available services will have
    registered with ZookeeperServiceRegistrar.

    This class will proxy all methods and attributes to the
    underlying service object. If no service is available,
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
            service_class=None, transport_class=None, protocol_class=None):
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
                provided TSocket will be used. If zookeeper_client
                is an instance of GZookeeperClient, TSocke will be
                appropriately patched for gevent comptability.
            protocol_class: Option Thrift protocol class. If not
                provided this will default to TBinaryProtocol.
        """
        self.zookeeper_client = zookeeper_client
        self.service_name = service_name
        self.service_class = service_class or TRService
        self.protocol_class = protocol_class or TBinaryProtocol.TBinaryProtocol
        self.registrar = ZookeeperServiceRegistrar(self.zookeeper_client)
        self.registry_path = os.path.join("/services", self.service_name, "registry")

        self.service = None        #Service client object
        self.service_node = None   #Service zookeeper node, i.e. chatsvc_00000001
        
        #Staged service client object and node.
        #If the the current self.service become unavailable
        #the _watcher() callback will be invoked asynchronously
        #by the zookeeper client. At this point, we'll create
        #a new service client object and stage it for update
        #on the next user invocation.
        self.staged_service = None
        self.staged_service_node = None
        
        #If using GZookeeperClient, we're in a gevent app and 
        #should adjust the Thrift transport, lock, and watch accordingly.
        if isinstance(self.zookeeper_client, GZookeeperClient):
            from trpycore.thrift_gevent.transport import TSocket
            self.transport_class = transport_class or TSocket.TSocket
            self.watch = GChildrenWatch(self.zookeeper_client, self.registry_path, self._watch)
            self.lock = self.NoOpLock()
        else:
            from thrift.transport import TSocket
            self.transport_class = transport_class or TSocket.TSocket
            self.watch = ChildrenWatch(self.zookeeper_client, self.registry_path, self._watch)
            self.lock = threading.Lock()
        
        #Acquire the lock, and create the service client.
        with self.lock:
            self.service_node, self.service = self._create_service()

        #Start watching zookeeper /services/<service_name>/registry for
        #addition and removal of service instances, so we can
        #update our proxy if our instance goes down.
        self.watch.start()
    
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
            
            node, service = self._create_service()
            
            #Update staged service and node.
            with self.lock:
                self.staged_service_node, self.staged_service = (node, service)
        
    def _create_service(self):
        """Create a new service client object.

        Returns:
            (Zookeeper node, Service) tuple if service is available,
            otherwise (None, None).
        """

        result = (None, None)
        
        #Locate an available service instance in the registrar
        path, registration = self.registrar.locate_zookeeper_service(self.service_name)

        #If a service instance is available, create the object and stage
        #it to be swapped in on the next user invocation.
        if path and registration:
            node = os.path.basename(path)
            transport = self.transport_class(registration.hostname, registration.port)
            protocol = self.protocol_class(transport)
            service = self.service_class.Client(protocol)

            try:
                transport.open()
            except Exception as error:
                logging.exception(error)

            result = (node, service)

        return result

    def __getattr__(self, attr):
        """Proxy all attributes to service object.

        This method will proxy all attribute requests
        to the underlying service object. This allow users
        to invoke service methods directrly through
        this class. 

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
        
        #If the service is unavailable raise ServiceProxyException.
        if self.service is None:
            raise ServiceProxyException("service unavailable")
        
        #Return service object attribute.
        return getattr(self.service, attr)


class ZookeeperServiceProxyPool(QueuePool):
    """Zookeeper service proxy pool.
    
    Creates a queue of ZookeeperServiceProxy objects for use across threads / greenlets
    depending on the chosen queue_class.

    Example usage:
        with pool.get() as service:
            service.getVersion(RequestContext())
    """
    
    def __init__(self, zookeeper_client, service_name, size, service_class=None, queue_class=Queue.Queue):
        """ZookeeperServiceProxyPool constructor.

        Args:
            zookeeper_client: Zookeeper client object.
            service_name: Service name, i.e. chatsvc
            service_class: Optional service class, i.e. TChatService.
                If not provided, TRService will be used which will
                only provide proxying to the service methods defined
                within TRService.
            size: Number of ZookeeperSessionStore objects to include in pool.
            queue_class: Optional queue class. If not provided, will
                default to Queue.Queue. The specified class must
                have a no-arg constructor and provide a get(block, timeout)
                method.
        """
        self.zookeeper_client = zookeeper_client
        self.service_name = service_name
        self.size = size
        self.service_class = service_class
        self.queue_class = queue_class
        super(ZookeeperServiceProxyPool, self).__init__(
                self.size,
                factory=self,
                queue_class=self.queue_class)
    
    def create(self):
        """ZookeeperServiceProxy factory method."""
        return ZookeeperServiceProxy(
                self.zookeeper_client,
                self.service_name,
                service_class=self.service_class)
