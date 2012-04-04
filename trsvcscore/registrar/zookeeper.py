import logging
import json
import os
import random
import socket
import Queue

from trsvcscore.registrar.base import ServiceRegistrar, ServiceRegistration, ServiceRegistrationEncoder

class ZookeeperServiceRegistrar(ServiceRegistrar):
    def __init__(self, zookeeper_client):
        self.zookeeper_client = zookeeper_client
        self.registration_queue = Queue.Queue()
        self.zookeeper_client.add_session_observer(self._session_observer)
    
    def _session_observer(self, event):
        if event.state_name == "CONNECTED_STATE":
            while not self.registration_queue.empty():
                registration = self.registration_queue.get()
                try:
                    self._register(registration)
                except Exception as error:
                    logging.error("Registration for %s failed" % (registration.name))
                    logging.exception(error)

    def _register(self, registration):
        if not self.zookeeper_client.connected:
            raise RuntimeError("Zookeeper client not connected")

        service_path = os.path.join("/services", registration.name)
        service_node = os.path.join(service_path, registration.name)
        
        self.zookeeper_client.create_path(service_path)
        self.zookeeper_client.create(
                service_node,
                json.dumps(registration, cls=ServiceRegistrationEncoder),
                sequence=True,
                ephemeral=True)
        
        logging.info("Registration for %s completed" % (registration.name))

    def register_service(self, service_name, service_port):
        if service_name is None or service_port is None:
            raise ValueError("service_name and service_port required for registration")

        registration = ServiceRegistration(service_name, service_port)

        try:
            self._register(registration)

        except Exception as error:
            logging.warning("Registartion for %s deferred: %s" % (service_name, str(error)))
            self.registration_queue.put(registration)

    def locate_service(self, name, host_affinity=True):
        result = None

        services = []
        path = os.path.join("/services", name)
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

        return result

    def find_services(self, name):
        result = []
        path = os.path.join("/services", name)
        for child in self.zookeeper_client.get_children(path):
            service_node = os.path.join(path, child)
            data, stat = self.zookeeper_client.get_data(service_node)
            result.append(ServiceRegistration.from_json(data))
        return result
