import logging
import json
import os
import random
import socket
import Queue

from trsvcscore.registrar.base import ServiceRegistrar
from trsvcscore.service.base import ServiceInfo

class ZookeeperServiceRegistrar(ServiceRegistrar):
    """Zookeeper service registrar."""
    def __init__(self, zookeeper_client):
        """ZookeeperServiceRegistrar constructor.

        Args:
            zookeeper_client: zookeeper client instance.
        """
        self.zookeeper_client = zookeeper_client
        self.registration_queue = Queue.Queue()
        self.registered_service_node = None
        self.log = logging.getLogger("%s.%s" % (__name__, self.__class__.__name__))

        self.zookeeper_client.add_session_observer(self._session_observer)
    
    def _session_observer(self, event):
        """Internal zookeeper session observer to handle deferred service registration.

        In the event that a service is registered while a zookeeper connection is not
        available the registration will be deferred until a connection with the zookeeper
        service is reestablished.

        Args:
            event: ZookeeperClient.Event
        """
        if event.state_name == "CONNECTED_STATE":
            while not self.registration_queue.empty():
                service = self.registration_queue.get()
                try:
                    self._register(service)
                except Exception as error:
                    self.log.error("Registration for %s failed" % (service.name()))
                    self.log.exception(error)

    def _register(self, service):
        """Register service with zookeeper.
        
        Register service with zookeeper by creating an ephemeral
        node at /services/<service>/registry. The data associated
        with the node will be a json representation of the
        ServiceInfo object.

        Args:
            server: Service object
        Raises: RuntimeError if registration fails.
        """
        if not self.zookeeper_client.connected:
            raise RuntimeError("Zookeeper client not connected")
        
        service_info = service.info()
        service_path = os.path.join("/services", service_info.name, "registry")
        service_node = os.path.join(service_path, service_info.name)
        
        self.zookeeper_client.create_path(service_path)
        self.zookeeper_client.create(
                service_node,
                json.dumps(service_info.to_json()),
                sequence=True,
                ephemeral=True)

        self.registered_service_node = service_node
        
        self.log.info("Registration for %s completed" % (service_info.name))

    def register_service(self, service):
        """Register a service with the registrar.

        If zookeeper connection is unavailable when this method is invoked,
        the registration will be deferred until the zookeeper client 
        successuflly reestablishes the connection. As soon as the
        connection is reestablished, the service will be registered.

        Args
            service: Service object
        """
        result = False
        try:
            self._register(service)
            result = True

        except Exception as error:
            service_info = service.info()
            self.log.warning("Registartion for %s deferred: %s" % (service_info.name, str(error)))
            self.registration_queue.put(service)
        
        return result

    def unregister_service(self):
        """Unregister a previously registered service with the registrar.

        If zookeeper connection is unavailable when this method is invoked,
        the service will be considered unregistered.
        """

        result = False
        try:
            if self.registered_service_node:
                self.zookeeper_client.delete(self.registered_service_node)
                result = True
            else:
                result = True

        except Exception as error:
            self.log.warning("Unregistartion for %s failed (considered service unregistered): %s" % (self.registered_service_node, str(error)))
        
        return result

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
        result = None
        
        try:
            services = []
            path = os.path.join("/services", name, "registry")
            for child in self.zookeeper_client.get_children(path):
                service_node = os.path.join(path, child)
                data, stat = self.zookeeper_client.get_data(service_node)
                services.append(ServiceInfo.from_json(data))
            
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
            (Zookeeper service node path, ServiceInfo) tuple if service is located,
            (None, None) otherwise.
        """
        result = (None, None)
        
        try:
            services = {}

            path = os.path.join("/services", name, "registry")
            for child in self.zookeeper_client.get_children(path):
                service_node = os.path.join(path, child)
                data, stat = self.zookeeper_client.get_data(service_node)
                services[os.path.join(path, child)] = ServiceInfo.from_json(data)
            
            if services:
                #If host affinity is set try to find a service on this host
                if host_affinity:
                    hostname = socket.gethostname()
                    host_services = {p: s for p, s in services.items() if s.hostname == hostname }
                    if host_services:
                        service_path = random.choice(host_services.keys())
                        result = (service_path, services[service_path])
                
                #If still no result, pick one at random
                if result is None:
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
            list of ServiceInfo objects for found services.
        """
        result = []

        try:
            path = os.path.join("/services", name, "registry")
            for child in self.zookeeper_client.get_children(path):
                service_node = os.path.join(path, child)
                data, stat = self.zookeeper_client.get_data(service_node)
                result.append(ServiceInfo.from_json(data))
        except Exception as error:                    
            self.log.exception(error)

        return result
