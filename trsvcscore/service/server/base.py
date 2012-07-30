import abc
import json

class ServerProtocol(object):
    """Server protocol enum."""
    THRIFT = "thrift"

class ServerTransport(object):
    """Server transport enum."""
    TCP = "tcp"
    ZMQ = "zmq"

class ServerEndpoint(object):
    """Server endpoint.

    Each server exposes functionallity through one or more endpoints.
    Each endpoint contains all the details necessary for a client
    to connect to it.
    """
    def __init__(self, address, port, protocol, transport):
        """ServerEndpoint constructor.

        Args:
            address: Server address string in the form of a
                hostname, fqdn, or ip address.
            port: Server port (int)
            protocol: ServerProtocol enum
            transport: ServerTransport enum
        """
        self.address = address
        self.port = port
        self.protocol = protocol
        self.transport = transport

    @staticmethod
    def from_json(data):
        """Convert json data to ServerEndpoint object.

        Args:
            data: json representation of the ServerEndpoint object,
                as either a json string or python dict.
        Returns:
            ServerEndpoint object
        """
        if isinstance(data, basestring):
            json_dict = json.loads(data)
        else:
            json_dict = data

        return ServerEndpoint(
                json_dict["address"],
                json_dict["port"],
                json_dict["protocol"],
                json_dict["transport"])

    def to_json(self):
        """Convert ServerEndpoint object to json representation.

        Returns:
            Python dict json representation. 
        """
        return {
            "address": self.address,
            "port": self.port,
            "protocol": self.protocol,
            "transport": self.transport
        }

class ServerInfo(object):
    """Server information.

    This class contains general information about the server and
    each of its endpoints in the form of ServerEndpoint objects.
    """
    def __init__(self, name, endpoints):
        """ServerInfo constructor.

        Args:
            name: server name, i.e. chatsvc-thrift
            endpoints: list of ServerEndpoint objects.
        """
        self.name = name
        self.endpoints = endpoints or []

    @staticmethod
    def from_json(data):
        """Convert json data to ServerInfo object.

        Args:
            data: json representation of the ServerInfo object,
                as either a json string or python dict.
        Returns:
            ServerInfo object
        """
        if isinstance(data, basestring):
            json_dict = json.loads(data)
        else:
            json_dict = data

        endpoints = []
        for json_endpoint in json_dict["endpoints"]:
            endpoints.append(ServerEndpoint.from_json(json_endpoint))
        
        return ServerInfo(json_dict["name"], endpoints)

    def to_json(self):
        """Convert ServerInfo object to json representation.

        Returns:
            Python dict json representation. 
        """
        json_endpoints = [l.to_json() for l in self.endpoints]
        return {
            "name": self.name,
            "endpoints": json_endpoints
        }

class Server(object):
    """Server abstract base class.
    
    Services consist of one or more servers, which expose portions of the
    service interface through one or more endpoints. Each server fulfills
    the service interface through delegation to Handler's.
    """
    __metaclass__ = abc.ABCMeta
    
    @abc.abstractmethod
    def start(self):
        """Start the server."""
        return

    @abc.abstractmethod
    def stop(self):
        """Stop the server."""
        return

    @abc.abstractmethod
    def join(self, timeout=None):
        """Join the server.

        Join the server, waiting for the completion of all threads 
        or greenlets.

        Args:
            timeout: Optional timeout in seconds to observe before returning.
                If timeout is specified, the status() method must be called
                to determine if the service is still running.
        """
        return

    @abc.abstractmethod
    def status(self):
        """Get server status.

        Returns:
            Status enum.
        """
        return

    @abc.abstractmethod
    def info(self):
        """Get server info.

        Returns:
            ServerInfo object.
        """
        return
