import json
import os
import socket

from trpycore.zookeeper_gevent.client import GZookeeperClient
from trpycore.zookeeper_gevent.watch import GHashringWatch
from trpycore.zookeeper.watch import HashringWatch

class ZookeeperServiceHashring(object):
    """Consistent service hashring.

    Wrapper around GHashringWatch to ensure consitencies for hashring
    implementations across services. ZookeeperServiceHashring should
    be used by both clients of the service and instances of the services
    needing to register positions on the hashring.
    
    All hashring position nodes are ephemeral and will automatically be 
    removed upon service disconnection or termination.
    
    A hashring node will be created in zookeeper at /services/<service>/hashring,
    where each child node will represent an occupied position on the hashring.
    The node name of each position (child) is a unique hash which will be used
    to determine the appropriate service for the given service (sharding).

    In order to route the data (sharding) a hash of the data will be
    computed and compared against the hashring position hashes.
    The first position to the right of the request or data's hash is the
    position responsible for processing the request or data.

    The data associated with each hashring position is a service specific
    dict of key /values (string) which should contain the details necessary
    for the user of the hashring to route their request. The
    dict will always contain the service name, port, hostname, and fqdn. Additional
    data can be added by services registering positions in the ring.
    """
    def __init__(self, zookeeper_client, service_name, service_port=None, num_positions=0, data=None):
        """ZookeeperServiceHashring constructor.

        Args:
            zookeeper_client: zookeeper client instance
            service_name: service name, i.e. chatsvc
            service_port: service port which is only required for services
                registering positions on the hashring.
            num_positions: Number of positions to register on the hashring
            data: Dict of additional key /values (string) to store with
                the hashring position nodes. The service name,
                port, hostname, and fqdn will always be stored.
        """
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
        """Start watching the hashring and register positions if needed."""
        self.hashring_watch.start()

    def stop(self):
        """Stop watching the hashring."""
        self.hashring_watch.stop()
    
    def get_children(self):
        """Get all of the hashring children nodes.

        Returns:
            Dict of position (node name) / data values (string)
        """
        return self.hashring_watch.get_children()

    def get_hashring(self):
        """Get hashring positions.

        Returns:
            A sorted list of hashring positions (node names)
        """
        return self.hashring_watch.get_hashring()

    def get_service(self, data):
        """Get the service responsible for this piece of data.

        Args:
            data: string value which will be hashed to determine
                the appropriate service instance for this data.


        In order to route the data (sharding) a hash of the data will be
        computed and compared against the hashring position hashes.
        The first position to the right of the request or data's hash is the
        position responsible for processing the request or data.
        
        Returns:
            Dict of key / values (string) for the selected service.
            Guaranteed to contain the service name, port,
            hostname, and fqdn.
        """
        service_data, stat = self.hashring_watch.get_hashchild(data)
        return json.loads(service_data)
