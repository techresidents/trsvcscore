import abc
import json

from trsvcscore.service.server.base import ServerInfo, ServerProtocol, ServerTransport

class ServiceInfo(object):
    """Service information class.

    This class encapsulates general service information, as well
    as general information about each of its servers in the form
    ServerInfo objects.
    """
    def __init__(self, name, version, build, hostname, fqdn, key, servers):
        """ServiceInfo constructor.

        Args:
            name: service name, i.e. chatsvc
            version: service version as string
            build: service build number as string
            hostname: service hostname
            fqdn: service fully qualified domain name
            servers: list of ServerInfo objects
            key: unique service key identifier
        """
        self.name = name
        self.version = version
        self.build = build
        self.hostname = hostname
        self.fqdn = fqdn
        self.key = key
        self.servers = servers
    
    @staticmethod
    def from_json(data):
        """Convert json data to ServiceInfo object.

        Args:
            data: json representation of the ServiceInfo object,
                as either a json string or python dict.
        Returns:
            ServiceInfo object
        """
        if isinstance(data, basestring):
            json_dict = json.loads(data)
        else:
            json_dict = data

        servers = [ServerInfo.from_json(s) for s in json_dict["servers"]]

        result = ServiceInfo(
                json_dict["name"],
                json_dict["version"],
                json_dict["build"],
                json_dict["hostname"],
                json_dict["fqdn"],
                json_dict["key"],
                servers)

        return result
 
    def __repr__(self):
        return "%s(%s, %s, %s, %s, %s, %s, %r)" % (
                self.__class__.__name__,
                self.name,
                self.version,
                self.build,
                self.hostname,
                self.fqdn,
                self.key,
                self.servers)

    def __str__(self):
        default_endpoint = self.default_endpoint()
        return "%s(name=%s, key=%s, default_endpoint=(%s, %s))" % (
                self.__class__.__name__,
                self.name,
                self.key,
                default_endpoint.address,
                default_endpoint.port)

    def default_endpoint(self):
        """Get the default Thrift server endpoint.
        
        Finds and return the default TCP/Thrift endpoint
        if it exists. This is the most common endpoint used
        by services for communication, so this method
        is provided as a convenience.

        Returns:
            ServerEndpoint object if it exists, None otherwise.
        """
        for server in self.servers:
            for endpoint in server.endpoints:
                if endpoint.protocol ==  ServerProtocol.THRIFT and \
                        endpoint.transport == ServerTransport.TCP:
                            return endpoint
        return None

    def to_json(self):
        """Convert ServiceInfo object to json representation.

        Returns:
            Python dict json representation. 
        """
        json_servers = [s.to_json() for s in self.servers]
        return {
            "name": self.name,
            "version": self.version,
            "build": self.build,
            "hostname": self.hostname,
            "fqdn": self.fqdn,
            "key": self.key,
            "servers": json_servers
        }

class Service(object):
    """Service abstract base class.
    
    A service is responsible for exposing the functionallity outlined in its service
    interface. The details of the service interface contract are defined in the form of
    a Thrift IDL.     

    Each Service consist of one or more servers, which expose portions of the
    service interface through one or more endpoints. Each server fulfills
    the service interface through delegation to its Handler's.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def name(self):
        """Get the service name, i.e. chatsvc

        Returns:
            Service name
        """
        return

    @abc.abstractmethod
    def version(self):
        """Get the service version.

        Returns:
            Service version as a string.
        """
        return

    @abc.abstractmethod
    def build(self):
        """Get the service build number.

        Returns:
            Service build number as a string.
        """
        return
   

    @abc.abstractmethod
    def start(self):
        """Start the service."""
        return

    @abc.abstractmethod
    def stop(self):
        """Stop the service."""
        return

    @abc.abstractmethod
    def join(self, timeout=None):
        """Join the service.

        Join the service, waiting for the completion of all threads 
        or greenlets.

        Args:
            timeout: Optional timeout in seconds to observe before returning.
                If timeout is specified, the status() method must be called
                to determine if the service is still running.
        """
        return

    @abc.abstractmethod
    def status(self):
        """Get the service status.

        Returns:
            Status enum.
        """
        return

    @abc.abstractmethod
    def info(self):
        """Get service info.

        Returns:
            ServiceInfo object.
        """
        return
