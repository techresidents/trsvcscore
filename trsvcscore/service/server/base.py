import abc
import json

class ServerProtocol(object):
    THRIFT = "thrift"

class ServerTransport(object):
    TCP = "tcp"
    ZMQ = "zmq"

class ServerEndpoint(object):
    def __init__(self, address, port, protocol, transport):
        self.address = address
        self.port = port
        self.protocol = protocol
        self.transport = transport

    @staticmethod
    def from_json(data):
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
        return {
            "address": self.address,
            "port": self.port,
            "protocol": self.protocol,
            "transport": self.transport
        }

class ServerInfo(object):
    def __init__(self, endpoints):
        self.endpoints = endpoints or []

    @staticmethod
    def from_json(data):
        if isinstance(data, basestring):
            json_dict = json.loads(data)
        else:
            json_dict = data

        endpoints = []
        for json_endpoint in json_dict["endpoints"]:
            endpoints.append(ServerEndpoint.from_json(json_endpoint))
        
        return ServerInfo(endpoints)

    def to_json(self):
        json_endpoints = [l.to_json() for l in self.endpoints]
        return {
            "endpoints": json_endpoints
        }

class Server(object):
    __metaclass__ = abc.ABCMeta
    
    @abc.abstractmethod
    def start(self):
        return

    @abc.abstractmethod
    def stop(self):
        return

    @abc.abstractmethod
    def join(self, timeout=None):
        return

    @abc.abstractmethod
    def status(self):
        return

    @abc.abstractmethod
    def info(self):
        return
