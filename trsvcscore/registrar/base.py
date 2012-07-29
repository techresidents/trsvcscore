import abc

class ServiceRegistrar(object):
    """Abstract base class to be implemented by service registrars."""
    __metaclass__ = abc.ABCMeta
    
    @abc.abstractmethod
    def register_service(self, service):
        """Register a service with the registrar.
        
        Args
            service: Service object
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
