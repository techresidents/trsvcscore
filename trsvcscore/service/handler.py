import logging

from tridlcore.gen import TRService
from tridlcore.gen.ttypes import ServiceStatus

from trpycore.zookeeper.client import ZookeeperClient
from trsvcscore.registrar.zookeeper import ZookeeperServiceRegistrar


class ServiceHandler(TRService.Iface, object):
    """Base class for service handler."""

    def __init__(self, name, interface, port, version, build, zookeeper_hosts, database_connection=None):
        """GServiceHandler constructor.

        Args:
            name: service name, i.e. chatsvc
            interface: interface service is listening on, 0.0.0.0 for all.
            port: service port
            version: service version (string)
            build: service build number (string)
            zookeeper_hosts: list of zookeeper hosts, i.e. ["localhost:2181", "localdev:2181"]
            database_connection: optional database connection string
        """
        self.name = name
        self.interface = interface
        self.port = port
        self.version = version
        self.build = build
        self.options = {}
        self.counters = {}
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
        
        #service will be injected by service prior to start()
        self.service = None

    def start(self):
        """Start service handler."""
        if not self.running:
            self.running = True
            self.zookeeper_client.start()
            self.registrar.register_service(self.name, self.port)
    
    def join(self, timeout):
        """Join service handler."""
        self.zookeeper_client.join(timeout)
    
    def stop(self):
        """Stop service handler."""
        if self.running:
            self.running = False
            self.zookeeper_client.stop()

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
        return self.name

    def getVersion(self, requestContext):
        """Get service version.

        Args:
            requestContext: RequestContext object containing user information.
        
        Returns:
            service version (string)
        """
        return self.version or "Unknown"

    def getBuildNumber(self, requestContext):
        """Get service build number.

        Args:
            requestContext: RequestContext object containing user information.
        
        Returns:
            service build number (string)
        """
        return self.build or "Unknown"

    def getStatus(self, requestContext):
        """Get service status.

        Args:
            requestContext: RequestContext object containing user information.
        
        Returns:
            ServiceStatus constant
        """
        if self.running:
            return ServiceStatus.ALIVE
        else:
            return ServiceStatus.DEAD

    def getStatusDetails(self, requestContext):
        """Get service status details.

        Args:
            requestContext: RequestContext object containing user information.
        
        Returns:
            String description of the current ServiceStatus constant.
        """
        if self.running:
            return "Alive and well"
        else:
            return "Dead"

    def getCounters(self, requestContext):
        """Get service counters.

        Args:
            requestContext: RequestContext object containing user information.
        
        Returns:
            Dict of service specific counters.
        """
        return self.counters

    def getOption(self, requestContext, key):
        """Get service option.

        Args:
            requestContext: RequestContext object containing user information.
            key: Option name
        
        Returns:
            String value for the option.
        """
        return self.options[key]

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
