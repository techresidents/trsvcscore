import socket
import uuid

from trpycore.thread.util import join
from trsvcscore.service.base import Service, ServiceInfo

class DefaultService(Service):
    """Default service base class.
    
    A service is responsible for exposing the functionallity outlined in its service
    interface. The details of the service interface contract are defined in the form of
    a Thrift IDL.     

    Each Service consist of one or more servers, which expose portions of the
    service interface through one or more endpoints. Each server fulfills
    the service interface through delegation to its Handler's.

    This class is intended to be subclassed by concrete service implementations.
    """
    def __init__(self, name, version, build, servers, hostname=None, fqdn=None, key=None):
        """DefaultService constructor.

        Args:
            name: service name, i.e. chatsvc
            version: service version as string
            build: service build number as string
            servers: list of Server objects
            hostname: optional service hostname.
                If not provided, socket.gethostname()
                will be used.
            fqdn: optional service fully qualified domain name.
                If not provided, socket.getfqdn() will be 
                used.
            key: optional unique service key identifier. If not
                provided a randomly generated UUID will be used.
        """
        self._name = name
        self._version = version
        self._build = build
        self.servers = servers
        self.hostname = hostname or socket.gethostname()
        self.fqdn = fqdn or socket.getfqdn()
        self.key = uuid.uuid4().hex
        self.running = False
    
    def name(self):
        """Get the service name, i.e. chatsvc

        Returns:
            Service name
        """
        return self._name

    def version(self):
        """Get the service version.

        Returns:
            Service version as a string.
        """
        return self._version

    def build(self):
        """Get the service build number.

        Returns:
            Service build number as a string.
        """
        return self._build

    def start(self):
        """Start the service.

        Start service, by starting each of its servers.
        """
        if not self.running:
            self.running = True
            for server in self.servers:
                server.start()

    def stop(self):
        """Stop the service.

        Stop service, by stopping each of its servers.
        """
        if self.running:
            self.running = False
            for server in self.servers:
                server.stop()

    def join(self, timeout=None):
        """Join the service.

        Join the service, waiting for the completion of all threads 
        or greenlets.

        Args:
            timeout: Optional timeout in seconds to observe before returning.
                If timeout is specified, the status() method must be called
                to determine if the service is still running.
        """
        join(self.servers, timeout)

    def status(self):
        """Get the service status.
        
        Return the Status enum with the largest value,
        which corresponds to the least functioning status.

        Returns:
            Status enum.
        """
        result = None
        for server in self.servers:
            status = server.status()
            if result is None:
                result = status
            elif status > result:
                result = status
        return result

    def info(self):
        """Get service info.

        Returns:
            ServiceInfo object.
        """
        server_info = []
        for server in self.servers:
            server_info.append(server.info())
        
        result = ServiceInfo(
                name=self._name,
                version=self._version,
                build=self._build,
                hostname=self.hostname,
                fqdn=self.fqdn,
                key=self.key,
                servers=server_info)

        return result
