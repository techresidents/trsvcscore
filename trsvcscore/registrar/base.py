import abc
import json
import socket


class ServiceRegistration(object):
    """Service registration record."""
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
    """JSON ServiceRegistraion encoder."""
    def default(self, obj):
        if isinstance(obj, ServiceRegistration):
            return obj.to_json()
        else:
            return super(ServiceRegistrationEncoder).default(self, obj)


class ServiceRegistrar(object):
    """Abstract base class to be implemented by service registrars."""
    __metaclass__ = abc.ABCMeta
    
    @abc.abstractmethod
    def register_service(self, service_name, service_port):
        """Register a service with the registrar.
        
        Args
            service_name: service name, i.e., chatsvc
            service_port: service port.
        """
        return

    @abc.abstractmethod
    def locate_service(self, name, host_affinity=True):
        """Locate a random service instance.

        Args:
            name: service name
            host_affinity: if True preference will be given to services
                located on the same physical host. Otherwise a service
                instance will be selected randomly.
        
        Returns:
            ServiceRegistration instance if service is located, None otherwise.
        """
        return
    
    @abc.abstractmethod
    def find_services(self, name):
        """Find all available instances of a service.

        Args:
            name: service name
        
        Returns:
            list of ServiceRegistration objects for found services.
        """
        return
