import logging

from tridlcore.gen import TRService
from tridlcore.gen.ttypes import Status

from trpycore.counter.atomic import AtomicCounters
from trpycore.zookeeper.client import ZookeeperClient
from trsvcscore.registrar.zookeeper import ZookeeperServiceRegistrar
from trsvcscore.service.handler.base import Handler


class ServiceHandler(TRService.Iface, Handler):
    """Service handler base class.
    
    This class is intended to be subclassed by concrete
    service handlers.
    """

    def __init__(self, service, zookeeper_hosts, database_connection=None):
        """ServiceHandler constructor.

        Args:
            service: Service object
            zookeeper_hosts: list of zookeeper hosts, i.e. ["localhost:2181", "localdev:2181"]
            database_connection: optional database connection string
        """
        self.service = service
        self.options = {}
        self.counters = AtomicCounters()
        self.running = False

        #Zookeeper client
        self.zookeeper_client = ZookeeperClient(zookeeper_hosts)

        #Database session factory
        if database_connection:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            engine = create_engine(database_connection)
            self.DatabaseSession = sessionmaker(bind=engine)
        else:
            self.DatabaseSession = None

        #Registrar
        self.registrar = ZookeeperServiceRegistrar(self.zookeeper_client)
        
        #Add counter decorator to track service method calls
        def counter_decorator(func):
            requests_counter = self.counters.get_counter("requests")
            open_requests_counter = self.counters.get_counter("open_requests")
            def wrapper(*args, **kwargs):
                try:
                    requests_counter.increment()
                    open_requests_counter.increment()
                    return func(*args, **kwargs)
                finally:
                    open_requests_counter.decrement()
            return wrapper
        self._decorate_service_methods(counter_decorator)

    def _decorate_service_methods(self, decorator, cls=None, decorated=None):
        """Decorate service interface methods at runtime.

        This method will decorate the service instance methods on the
        current handler with the given decorator. Service interface
        methods are identified as any callable on a base class
        with the name "Iface".

        This method should be used judicially to limit the magic.
        The main advantage of this method is that decorators can
        be added to all service methods from a base class,
        without specific knowledge of each service's interface.

        Derived classes should NOT add decorators using this method.
        """
        cls = cls or self.__class__
        decorated = decorated if decorated is not None else {}

        if cls.__name__ == "Iface":
            for attribute_name in cls.__dict__:
                attribute = getattr(self, attribute_name)
                if callable(attribute) and attribute_name not in decorated:
                    setattr(self, attribute_name, decorator(attribute))
                    decorated[attribute_name] = True
        
        for base_class in cls.__bases__:
            self._decorate_service_methods(decorator, base_class, decorated)

    def start(self):
        """Start service handler."""
        if not self.running:
            self.running = True
            self.zookeeper_client.start()
            self.registrar.register_service(self.service)
    
    def join(self, timeout):
        """Join service handler.

        Join the handler, waiting for the completion of all threads 
        or greenlets.

        Args:
            timeout: Optional timeout in seconds to observe before returning.
                If timeout is specified, the status() method must be called
                to determine if the handler is still running.
        """
        self.zookeeper_client.join(timeout)
    
    def stop(self):
        """Stop service handler."""
        if self.running:
            self.running = False
            self.zookeeper_client.stop()

    def status(self):
        """Get the handler status.

        Returns Status enum.
        """
        if self.running:
            return Status.ALIVE
        else:
            return Status.STOPPED

    def get_database_session(self):
        """Return new database SQLAlchemy database session.

        Returns:
            new SQLAlchemy session
        Raises:
            RuntimeError: If database_connection not provided to handler.
        """
        if self.DatabaseSession:
            return self.DatabaseSession()
        else:
            raise RuntimeError("database_connection not provided")

    def getName(self, requestContext):
        """Get service name.

        Args:
            requestContext: RequestContext object containing user information.
        
        Returns:
            service name (string)
        """
        return self.service.name()

    def getVersion(self, requestContext):
        """Get service version.

        Args:
            requestContext: RequestContext object containing user information.
        
        Returns:
            service version (string)
        """
        return self.service.version()

    def getBuildNumber(self, requestContext):
        """Get service build number.

        Args:
            requestContext: RequestContext object containing user information.
        
        Returns:
            service build number (string)
        """
        return self.service.build()

    def getStatus(self, requestContext):
        """Get service status.

        Args:
            requestContext: RequestContext object containing user information.
        
        Returns:
            Status enum
        """
        return self.service.status()

    def getStatusDetails(self, requestContext):
        """Get service status details.

        Args:
            requestContext: RequestContext object containing user information.
        
        Returns:
            String description of the current Status enum.
        """
        if self.running:
            return "Alive and well"
        else:
            return "Dead"

    def getCounter(self, requestContext, key):
        """Get service counter.

        Args:
            requestContext: RequestContext object containing user information.
            key: counter name
        
        Returns:
            counter value
        """
        if key in self.counters:
            return self.counters[key]
        else:
            return -1

    def getCounters(self, requestContext):
        """Get service counters.

        Args:
            requestContext: RequestContext object containing user information.
        
        Returns:
            Dict of service specific counters.
        """
        return self.counters.as_dict()

    def getOption(self, requestContext, key):
        """Get service option.

        Args:
            requestContext: RequestContext object containing user information.
            key: Option name
        
        Returns:
            String value for the option.
        """
        if key in self.options:
            return self.options[key]
        else:
            return "invalid option"

    def getOptions(self, requestContext):
        """Get all service options.

        Args:
            requestContext: RequestContext object containing user information.
        
        Returns:
            Dict of service specific options  key / values.
        """
        return self.options

    def setOption(self, requestContext, key, value):
        """Set service options.

        Args:
            requestContext: RequestContext object containing user information.
            key: Option name (string)
            value: Option value
        """
        self.options[key] = value

    def shutdown(self, requestContext):
        """Shutdown service.

        Args:
            requestContext: RequestContext object containing user information.
        """
        self.service.stop()

    def reinitialize(self, requestContext):
        """Reinitialize service.

        Args:
            requestContext: RequestContext object containing user information.
        """
        pass
