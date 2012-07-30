import abc
import json

from trsvcscore.service.server.base import ServerInfo

class ServiceInfo(object):
    """Service information class.

    This class encapsulates general service information, as well
    as general information about each of its servers in the form
    ServerInfo objects.
    """
    def __init__(self, name, version, build, hostname, fqdn, servers):
        """ServiceInfo constructor.

        Args:
            name: service name, i.e. chatsvc
            version: service version as string
            build: service build number as string
            hostname: service hostname
            fqdn: service fully qualified domain name
            servers: list of ServerInfo objects
        """
        self.name = name
        self.version = version
        self.build = build
        self.hostname = hostname
        self.fqdn = fqdn
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
                servers)

        return result

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
