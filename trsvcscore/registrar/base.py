import abc

class ServiceRegistrar(object):
    """Abstract base class to be implemented by service registrars."""
    __metaclass__ = abc.ABCMeta
    
    @abc.abstractmethod
    def register_service(self, service):
        """Register a service with the registrar.
        
        Register a service with the registrar. Failed registrations,
        due to connectivity issues, will be deferred and automatically
        retried upon connection reestablishment.
        
        Args
            service: Service object
        Returns: True if service was registered, False if registration
            was deferred.
        """
        return

    @abc.abstractmethod
    def unregister_service(self, service):
        """Unregister a previously registered service with the registrar.

        Unegister a service with the registrar. Failed registrations,
        due to connectivity issues, will be deferred and automatically
        retried upon connection reestablishment.

        Args:
            service: Service object

        Returns: True if service was unregistered, False if unregistration
            was deferred.
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
            ServiceInfo object if service is located, None otherwise.
        """
        return
    
    @abc.abstractmethod
    def find_services(self, name):
        """Find all available instances of a service.

        Args:
            name: service name
        
        Returns:
            list of ServiceInfo objects for found services.
        """
        return
