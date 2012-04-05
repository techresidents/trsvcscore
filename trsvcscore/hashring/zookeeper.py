import json
import os
import socket

from trpycore.zookeeper_gevent.client import GZookeeperClient
from trpycore.zookeeper_gevent.watch import GHashringWatch
from trpycore.zookeeper.watch import HashringWatch

class ZookeeperServiceHashring(object):
    def __init__(self, zookeeper_client, service_name, service_port=None, num_positions=0, data=None):
        self.zookeeper_client = zookeeper_client
        self.service_name = service_name
        self.num_positions = num_positions
        self.data = {
            "service": service_name,
            "service_port": service_port,
            "hostname": socket.gethostname(),
            "fqdn": socket.getfqdn()
        }

        if data:
            self.data.update(data)

        self.path = os.path.join("/services", service_name, "hashring")
        
        #Determine hashring class based on zookeeper client
        if isinstance(self.zookeeper_client, GZookeeperClient):
            hashring_class = GHashringWatch
        else:
            hashring_class = HashringWatch
        
        #Create hash ring
        self.hashring_watch = hashring_class(
                client=self.zookeeper_client,
                path=self.path,
                num_positions=self.num_positions,
                position_data=json.dumps(self.data))

    def start(self):
        self.hashring_watch.start()

    def stop(self):
        self.hashring_watch.stop()
    
    def get_children(self):
        return self.hashring_watch.get_children()

    def get_hashring(self):
        return self.hashring_watch.get_hashring()

    def get_service(self, data):
        service_data, stat = self.hashring_watch.get_hashchild(data)
        return json.loads(service_data)
