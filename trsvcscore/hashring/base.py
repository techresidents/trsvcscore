import abc

class ServiceHashringException(Exception):
    pass

class ServiceHashringNode(object):
    """Service hashring node class."""

    def __init__(self, token, service_info, data=None):
        """ServiceHashringNode constructor.

        Args:
            token: 128-bit integer token identifying the node's
                position on the hashring.
            service_info: ServiceInfo object identifying the service
                occupying the node.
            data: addtional dict of data stored at the node.
        """

        self.token = token
        self.service_info = service_info
        self.data = data or {}

    def __cmp__(self, other):
        if self.token < other.token:
            return -1
        elif self.token > other.token:
            return 1
        else:
            return 0
    
    def __hash__(self):
        return self.token.__hash__()

    def __repr__(self):
        return "%s(%s, %r, %r)" % (
                self.__class__.__name__,
                self.token,
                self.service_info,
                self.data)

    def __str__(self):
        return "%s(%x, %s)" % (
                self.__class__.__name__,
                self.token,
                self.service_info)


class ServiceHashringEvent(object):
    """Service hashring event."""
    
    CONNECTED_EVENT = "CONNECTED_EVENT"
    CHANGED_EVENT = "CHANGED_EVENT"
    DISCONNECTED_EVENT = "DISCONNECTED_EVENT"

    def __init__(self, event_type, previous_hashring=None, current_hashring=None,
            added_nodes=None, removed_nodes=None):
        """ServiceHashringEvent constructor.

        Args:
            event_type: event type (ALL EVENTS)
            previous_hashring: list of ServiceHashringNode's before change (CHANGED_EVENT)
            current_hashring: list of ServiceHashringNode's after change (CHANGED_EVENT)
            added_nodes: list of added ServiceHashringNode's (CHANGED_EVENT)
            removed_nodes: list of removed ServiceHashringNode's (CHANGED_EVENT)
        """
        self.event_type = event_type
        self.previous_hashring = previous_hashring
        self.current_hashring = current_hashring
        self.added_nodes = added_nodes
        self.removed_nodes = removed_nodes
    
    def __repr__(self):
        return "%s(%r, %r, %r, %r %r)" % (
                self.event_type,
                self.previous_hashring,
                self.current_hashring,
                self.added_nodes,
                self.removed_nodes)

class ServiceHashring(object):
    """Consistent service hashring abstract base class.
    
    This class represents a consistent hashring where the
    positions are occupied by services. Each occupied position on
    the hashring is considered a node, and is represented by the
    ServiceHashringNode class.  Each node is assigned a unique token
    which identifies its place on the hashring, and is used to determine
    which node is responsible for requests related to a
    specific piece of data.

    Note that it is possible, and advisiable that a single service
    occupy more than one position on the hashring.  This will
    promote a more even load balancing, and also allows
    more powerful machines to occupy more positions to take on
    a greater portion of the load.

    This class is designed to be used by both services occupying
    positions on the hashring, and services which are simply
    observing the hashring.
    
    In order to route a service request, a hash of the governing data
    is computed. The hashring is then traversed in a clockwise direction
    to determine the appropriate node for the given data.
    The first node whose token is greater than the data's hash
    is responsible for processing the request or data.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, service_name, service=None, positions=None, position_data=None):
        """ServiceHashring constructor.

        Args:
            service_name: service name, i.e. chatsvc
            service: optional Service object which is only required for services
                registering positions on the hashring.
            positions: optional list of positions to occupy on the
                hashring (nodes to create). Each position
                must be a 128-bit integer in integer or hex string format.
                If None, a randomly generated position will be used.
                Note that in the case of a position collision, a
                randomly generated position will also be used.
            position_data: Dict of additional key /values (string) to store with
                the hashring position node. 
        """

        self.service_name = service_name
        self.service = service
        self.positions = positions
        self.position_data = position_data or {}

    @abc.abstractmethod
    def start(self):
        """Start watching the hashring and register positions if needed."""
        self.hashring_watch.start()

    @abc.abstractmethod
    def stop(self):
        """Stop watching the hashring and remove positions if needed."""
        return

    @abc.abstractmethod
    def join(self, timeout):
        """Join the hashring."""
        return

    @abc.abstractmethod
    def add_observer(self, method):
        """Add a hashring observer method.

        The given method will be invoked with following arguments:
            hashring: ServiceHashring object
            event: ServiceHashringEvent object
        """
        return

    @abc.abstractmethod
    def remove_observer(self, method):
        """Remove a hashring observer method."""
        return

    @abc.abstractmethod
    def hashring(self):
        """Return hashring as ordered list of ServiceHashringNode's.
        
        Hashring is represented as an ordered list of ServiceHashringNode's.
        The list is ordered by hashring position (ServiceHashringNode.token).

        Returns:
            Ordered list of ServiceHashringNode's.
        """
        return

    @abc.abstractmethod
    def preference_list(self, data, merge_nodes=True):
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
        return

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
        return
