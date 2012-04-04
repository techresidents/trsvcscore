import abc
import json
import socket


class ServiceRegistration(object):
    def __init__(self, service_name, service_port, hostname=None, fqdn=None):
        self.name = service_name
        self.port = service_port
        self.hostname = hostname or socket.gethostname()
        self.fqdn = fqdn or socket.getfqdn()
    
    @staticmethod
    def from_json(data):
        json_dict = json.loads(data)
        return ServiceRegistration(
                json_dict["name"],
                json_dict["port"],
                json_dict["hostname"],
                json_dict["fqdn"])

    def to_json(self):
        return {
            "name": self.name,
            "port": self.port,
            "hostname": self.hostname,
            "fqdn": self.fqdn
        }


class ServiceRegistrationEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ServiceRegistration):
            return obj.to_json()
        else:
            return super(ServiceRegistrationEncoder).default(self, obj)


class ServiceRegistrar(object):
    __metaclass__ = abc.ABCMeta
    
    @abc.abstractmethod
    def register_service(self, service_name, service_port):
        return

    @abc.abstractmethod
    def locate_service(self, name, host_affinity=True):
        return
    
    @abc.abstractmethod
    def find_services(self, name):
        return
