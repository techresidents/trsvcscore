import json
import logging
import os

from trpycore.zookeeper_gevent.client import GZookeeperClient
from trpycore.zookeeper_gevent.watch import GHashringWatch
from trpycore.zookeeper.watch import HashringWatch
from trsvcscore.hashring.base import ServiceHashring, ServiceHashringNode, ServiceHashringException, ServiceHashringEvent

class ZookeeperServiceHashring(ServiceHashring):
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
    def __init__(self, zookeeper_client, service_name,
            service_port=None, positions=None, position_data=None):
        """ZookeeperServiceHashring constructor.

        Args:
            zookeeper_client: zookeeper client instance
            service_name: service name, i.e. chatsvc
            service_port: service port which is only required for services
                registering positions on the hashring.
            positions: optional list of positions to occupy on the
                hashring (nodes to create). Each position
                must be a uuid hex string or None. If None, a randomly
                generated position will be used. Note that in the 
                case of a position collision, a randomly generated
                position will also be used.
            position_data: Dict of additional key /values (string) to store with
                the hashring position node. At a minimum, the service_name,
                service_port, service_key, hostname, and fqdn will be
                stored.
        """
        super(ZookeeperServiceHashring, self).__init__(
                service_name=service_name,
                service_port=service_port,
                positions=positions,
                position_data=position_data)

        self.zookeeper_client = zookeeper_client
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
                positions=self.positions,
                position_data=json.dumps(self.position_data),
                watch_observer=self._watch_observer,
                session_observer=self._session_observer)

        self.observers = []

    def start(self):
        """Start watching the hashring and register positions if needed."""
        self.hashring_watch.start()

    def stop(self):
        """Stop watching the hashring and remove positions if needed."""
        self.hashring_watch.stop()
    
    def join(self, timeout=None):
        """Join the hashring."""
        return self.hashring_watch.join(timeout)

    def add_observer(self, method):
        """Add a hashring observer method.

        The given method will be invoked with following arguments:
            hashring: ServiceHashring object
            event: ServiceHashringEvent object
        """
        self.observers.append(method)

    def remove_observer(self, method):
        """Remove a hashring observer method."""
        self.observers.remove(method)
    
    def children(self):
        """Return hashring node's children.
        
        The children node names represent positions on the hashring.

        Returns:
            dict with the node name as the key and its (data, stat) as its value.
        """
        return self.hashring_watch.get_children()

    def hashring(self):
        """Return hashring as ordered list of ServiceHashringNode's.
        
        Hashring is represented as an ordered list of ServiceHashringNode's.
        The list is ordered by hashring position (ServiceHashringNode.token).

        Returns:
            Ordered list of ServiceHashringNode's.
        """
        nodes = self.hashring_watch.hashring()
        return self._convert_hashring_nodes(nodes)

    def preference_list(self, data, hashring=None, merge_nodes=True):
        """Return a preference list of ServiceHashringNode's for the given data.
        
        Generates an ordered list of ServiceHashringNode's responsible for
        the data. The list is ordered by node preference, where the
        first node in the list is the most preferred node to process
        the data. Upon failure, lower preference nodes in the list
        should be tried.

        Note that each service (unique service_key) will only appear
        once in the perference list. For each service, The
        most preferred ServiceHashringNode will be returned.
        Removing duplicate service nodes make the preference
        list makes it easier to use for failure retries, and
        replication.

        Additionally, if the merge_nodes flag is True, each
        unique hostname will appear once in the preference
        list. The most perferred ServiceHashringNode per
        hostname will be returned. This is extremely
        useful for replication, since it's often a requirement
        that replication nodes be on different servers.
        
        Args:
            data: string to hash to find appropriate hashring position.
            hashring: Optional list of ServiceHashringNode's for which
                to calculate the preference list. If None, the current
                hashring will be used.
            merge_nodes: Optional flag indicating that each hostname
                should only appear once in the preference list. The
                most preferred ServiceHashringNode per hostname will
                be returned.
        Returns:
            Preference ordered list of ServiceHashringNode's responsible
            for the given data.
        """
        if hashring:
            hashring = self._unconvert_hashring_nodes(hashring)
        
        nodes = self.hashring_watch.preference_list(data, hashring)
        nodes = self._convert_hashring_nodes(nodes)
        
        results = []
        keys = {}
        hostnames = {}
        for node in nodes:
            if node.service_key not in keys:
                if node.hostname not in hostnames or not merge_nodes:
                    results.append(node)
                    hostnames[node.hostname] = True
                    keys[node.service_key] = True

        return results

    def find_hashring_node(self, data):
        """Find the hashring node responsible for the given data.

        The selected hashring node is determined based on the hash
        of the user passed "data". The first node to the
        right of the data hash on the hash ring
        will be selected.
        
        Args:
            data: string to hash to find appropriate hashring position.
        Returns:
            ServiceHashringNode responsible for the given data.
        Raises:
            ServiceHashringException if no nodes are available.
        """

        nodes = self.preference_list()
        if nodes:
            return nodes[0]
        else:
            raise ServiceHashringException("no services available (empty hashring)")

    def _convert_hashring_nodes(self, hashring_nodes):
        """Convert HashringNode's to ServiceHashringNode's.
        Returns:
            list of ServiceHashringNode's.
        """
        results = []
        for node in hashring_nodes or []:
            service_node = ServiceHashringNode(
                token=node.token,
                data=json.loads(node.data))
            results.append(service_node)
        return results

    def _unconvert_hashring_nodes(self, hashring_nodes):
        """Convert ServiceHashringNode's to HashringNode's.
        Returns:
            list of HashringNode's.
        """
        results = []
        for service_node in hashring_nodes or []:
            node = self.hashring_watch.HashringNode(
                token=service_node.token,
                data=json.dumps(service_node.data))
            results.append(node)
        return results

    def _watch_observer(self, hashring_watch, previous_hashring,
            current_hashring, added_nodes, removed_nodes):
        """Hashring watch observer

        Args:
            hashring_watch: HashringWatch object
            previous_hashring: HashringNode's prior to change
            current_hashring: HashringNode's following change
            added_nodes: added HashringNode's
            removed_nodes: removed HashringNode's
        """
        if self.observers:
            previous_hashring = self._convert_hashring_nodes(previous_hashring)
            current_hashring = self._convert_hashring_nodes(current_hashring)
            added_nodes = self._convert_hashring_nodes(added_nodes)
            removed_nodes = self._convert_hashring_nodes(removed_nodes)

            event = ServiceHashringEvent(
                    ServiceHashringEvent.CHANGED_EVENT,
                    previous_hashring,
                    current_hashring,
                    added_nodes,
                    removed_nodes)

            for observer in self.observers:
                try:
                    observer(self, event)
                except Exception as error:
                    logging.exception(error)

    def _session_observer(self, event):
        """Hashring watch session observer

        Args:
            event: Zookeeper.Client object.
        """
        if self.observers:
            if event.state_name == "CONNECTED_STATE":
                event = ServiceHashringEvent(ServiceHashringEvent.CONNECTED_EVENT)
            elif event.state_name == "CONNECTING_STATE":
                event = ServiceHashringEvent(ServiceHashringEvent.DISCONNECTED_EVENT)
            elif event.state_name == "SESSION_EXPIRED_STATE":
                event = ServiceHashringEvent(ServiceHashringEvent.DISCONNECTED_EVENT)
        
            for observer in self.observers:
                try:
                    observer(self, event)
                except Exception as error:
                    logging.exception(error)
