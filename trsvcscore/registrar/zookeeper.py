import logging
import json
import os
import random
import socket
import Queue

from trsvcscore.registrar.base import ServiceRegistrar, ServiceRegistration, ServiceRegistrationEncoder

class ZookeeperServiceRegistrar(ServiceRegistrar):
    """Zookeeper service registrar."""
    def __init__(self, zookeeper_client):
        """ZookeeperServiceRegistrar constructor.

        Args:
            zookeeper_client: zookeeper client instance.
        """
        self.zookeeper_client = zookeeper_client
        self.registration_queue = Queue.Queue()
        self.log = logging.getLogger("%s.%s" % (__name__, self.__class__.__name__))

        self.zookeeper_client.add_session_observer(self._session_observer)
    
    def _session_observer(self, event):
        """Internal zookeeper session observer to handle deferred service registration.

        In the event that a service is registered while a zookeeper connection is not
        available the registration will be deferred until a connection with the zookeeper
        service is reestablished.
        """
        if event.state_name == "CONNECTED_STATE":
            while not self.registration_queue.empty():
                registration = self.registration_queue.get()
                try:
                    self._register(registration)
                except Exception as error:
                    self.log.error("Registration for %s failed" % (registration.name))
                    self.log.exception(error)

    def _register(self, registration):
        """Register service with zookeeper."""
        if not self.zookeeper_client.connected:
            raise RuntimeError("Zookeeper client not connected")

        service_path = os.path.join("/services", registration.name, "registry")
        service_node = os.path.join(service_path, registration.name)
        
        self.zookeeper_client.create_path(service_path)
        self.zookeeper_client.create(
                service_node,
                json.dumps(registration, cls=ServiceRegistrationEncoder),
                sequence=True,
                ephemeral=True)
        
        self.log.info("Registration for %s completed" % (registration.name))

    def register_service(self, service_name, service_port):
        """Register a service with the registrar.

        If zookeeper connection is unavailable when this method is invoked,
        the registration will be deferred until the zookeeper client 
        successuflly reestablishes the connection. As soon as the
        connection is reestablished, the service will be registered.

        Args
            service_name: service name, i.e., chatsvc
            service_port: service port.
        """
        if service_name is None or service_port is None:
            raise ValueError("service_name and service_port required for registration")

        registration = ServiceRegistration(service_name, service_port)

        try:
            self._register(registration)

        except Exception as error:
            self.log.warning("Registartion for %s deferred: %s" % (service_name, str(error)))
            self.registration_queue.put(registration)

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
        result = None
        
        try:
            services = []
            path = os.path.join("/services", name, "registry")
            for child in self.zookeeper_client.get_children(path):
                service_node = os.path.join(path, child)
                data, stat = self.zookeeper_client.get_data(service_node)
                services.append(ServiceRegistration.from_json(data))
            
            if services:
                #If host affinity is set try to find a service on this host
                if host_affinity:
                    hostname = socket.gethostname()
                    host_services = [s for s in services if s.hostname == hostname]
                    if host_services:
                        result = random.choice(host_services)
                
                #If still no result, pick one at random
                result = result or random.choice(services)

        except Exception as error:
            self.log.exception(error)

        return result

    def locate_zookeeper_service(self, name, host_affinity=True):
        """Locate a random service instance.

        Equivalent to locate_service, except the result is a tuple including
        the zookeeper service node path. This is convenient if the user
        would like to add a watch to the service.

        Args:
            name: service name
            host_affinity: if True preference will be given to services
                located on the same physical host. Otherwise a service
                instance will be selected randomly.
        
        Returns:
            (Zookeeper service node path, ServiceRegistration) tuple if service is located,
            (None, None) otherwise.
        """
        result = (None, None)
        
        try:
            services = {}

            path = os.path.join("/services", name, "registry")
            for child in self.zookeeper_client.get_children(path):
                service_node = os.path.join(path, child)
                data, stat = self.zookeeper_client.get_data(service_node)
                services[os.path.join(path, child)] = ServiceRegistration.from_json(data)
            
            if services:
                #If host affinity is set try to find a service on this host
                if host_affinity:
                    hostname = socket.gethostname()
                    host_services = {p: s for p, s in services.items() if s.hostname == hostname }
                    if host_services:
                        service_path = random.choice(host_services.keys())
                        result = (service_path, services[service_path])
                
                #If still no result, pick one at random
                service_path = random.choice(host_services.keys())
                result = (service_path, services[service_path])

        except Exception as error:
            self.log.exception(error)

        return result

    def find_services(self, name):
        """Find all available instances of a service.

        Args:
            name: service name
        
        Returns:
            list of ServiceRegistration objects for found services.
        """
        result = []

        try:
            path = os.path.join("/services", name, "registry")
            for child in self.zookeeper_client.get_children(path):
                service_node = os.path.join(path, child)
                data, stat = self.zookeeper_client.get_data(service_node)
                result.append(ServiceRegistration.from_json(data))
        except Exception as error:                    
            self.log.exception(error)

        return result
