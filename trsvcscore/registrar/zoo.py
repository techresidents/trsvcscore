import logging
import json
import os
import random
import socket

import zookeeper

from trpycore.zookeeper_gevent.client import GZookeeperClient
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
        
        #Adjust queue for thread/greenlets accordingly.
        if isinstance(self.zookeeper_client, GZookeeperClient):
            import gevent.queue
            self.registration_queue = gevent.queue.Queue()
        else:
            import Queue
            self.registration_queue = Queue.Queue()

        #store map of registered service so we can
        #re-register them upon session expiration.
        #Note that this is necessary since registration
        #nodes are ephemeral.
        self.registered_services = {}
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
        if event.state == zookeeper.CONNECTED_STATE:
            while not self.registration_queue.empty():
                service = self.registration_queue.get()
                try:
                    self._register(service)
                except Exception as error:
                    self.log.error("Registration for %s failed" % (service.name()))
                    self.log.exception(error)
        elif event.state == zookeeper.EXPIRED_SESSION_STATE:
            #Add registeration jobs to queue for all registered services
            #so that services are re-registered when we re-connect.
            for service_node, service in self.registered_services.iteritems():
                self.registration_queue.put(service)

    
    def _service_node_path(self, service):
        """Returns the Zookeeper service node path for service."""
        service_info = service.info()
        service_path = os.path.join("/services", service_info.name, "registry")
        service_node = os.path.join(service_path, "%s_%s" % (service_info.name, service_info.key))
        return service_node

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
        service_node = self._service_node_path(service)
        
        try:
            self.zookeeper_client.create_path(
                    service_node,
                    json.dumps(service_info.to_json()),
                    sequence=False,
                    ephemeral=True)

            self.registered_services[service_node] = service

        except zookeeper.NodeExistsException:
            self.log.warning("Registration for %s not needed (already registered)." % service_info)

        self.log.info("Registration for %s completed" % service_info)

    def register_service(self, service):
        """Register a service with the registrar.

        If zookeeper connection is unavailable when this method is invoked,
        the registration will be deferred until the zookeeper client 
        successuflly reestablishes the connection. As soon as the
        connection is reestablished, the service will be registered.

        Args:
            service: Service object
        """
        result = False
        try:
            self._register(service)
            result = True

        except Exception as error:
            service_info = service.info()
            self.log.warning("Registartion for %s deferred: %s" % (service_info, str(error)))
            self.registration_queue.put(service)
        
        return result

    def unregister_service(self, service):
        """Unregister a previously registered service with the registrar.

        If zookeeper connection is unavailable when this method is invoked,
        the service will be considered unregistered.

        Args:
            service: Service object
        """
        result = False
        service_info = service.info()
        service_node = self._service_node_path(service)

        try:
            self.zookeeper_client.delete(service_node)

        except zookeeper.NoNodeException:
            result = True
            self.log.warning("Unregistration for %s not needed (already unregistered)." % service_info)
        except Exception as error:
            self.log.warning("Unregistartion for %s failed (considered service unregistered): %s" % (service_info, str(error)))
        
        if service_node in self.registered_services:
            del self.registered_services[service_node]

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
                if result[0] is None:
                    service_path = random.choice(services.keys())
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

    def find_zookeeper_services(self, name):
        """Find all available instances of a service.

        Equivalent to find_services except the result is a list of tuples
        including the zookeeper service node path. This is convenient if
        the user would like to add a watch to the service.

        Args:
            name: service name
        
        Returns:
            list of (Zookeeper node path, ServiceInfo) tuples for found services.
        """
        result = []

        try:
            path = os.path.join("/services", name, "registry")
            for child in self.zookeeper_client.get_children(path):
                service_node = os.path.join(path, child)
                data, stat = self.zookeeper_client.get_data(service_node)
                result.append((service_node, ServiceInfo.from_json(data)))
        except Exception as error:                    
            self.log.exception(error)

        return result
