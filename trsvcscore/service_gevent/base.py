import logging
import gevent

from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

from trpycore.greenlet.util import join
from trpycore.thrift_gevent.server import TGeventServer
from trpycore.thrift_gevent.transport import TSocket
from trpycore.mongrel2_gevent.handler import GConnection

class GService(object):
    """Base class for gevent services"""
    def __init__(self, name, interface, port, handler, processor,
            transport=None, transport_factory=None, protocol_factory=None):
        """GService constructor.

        Args:
            name: service name, i.e. chatsvc
            interface: interface for server to listen on, 0.0.0.0 for all.
            port: service port
            handler: GServiceHandler handler instance
            processor: Thrift service processor
            transport: optional Thrift transport class
            transport_factory: optional Thrift transport factory
            protocol_factory: optional Thrift protocol factory
        """
        
        self.name = name
        self.interface = interface
        self.port = port
        self.handler = handler
        self.processor = processor
        self.transport = transport or TSocket.TServerSocket(self.interface, self.port)
        self.transport_factory = transport_factory or TTransport.TBufferedTransportFactory()
        self.protocol_factory = protocol_factory or TBinaryProtocol.TBinaryProtocolFactory()
        self.greenlet = None
        self.running = False
        
        #Inject service into handler
        self.handler.service = self
    
    def start(self):
        """Start service."""
        if not self.running:
            self.running = True
            self.greenlet = gevent.spawn(self.run)
            self.handler.start()
    
    def run(self):
        while self.running:
            try:
                server = TGeventServer(self.processor, self.transport, self.transport_factory, self.protocol_factory)
                server.serve()

            except Exception as error:
                logging.exception(error)

            except gevent.GreenletExit:
                break
    
    def stop(self):
        """Stop service."""
        if self.running:
            self.running = False
            self.handler.stop()
            if self.greenlet:
                self.greenlet.kill()
    
    def join(self, timeout=None):
        """Join service."""
        if self.greenlet:
            join([self.handler, self.greenlet], timeout)
        else:
            self.handler.join(timeout)


class GMongrel2Service(GService):
    """Base class for gevent Mongrel2 services."""

    def __init__(self, name,  interface, port, processor, handler,
            mongrel2_sender_id, mongrel2_pull_addr, mongrel2_pub_addr,
            transport=None, transport_factory=None, protocol_factory=None):
        """GMongrel2Service constructor.
        Args:
            name: service name, i.e. chatsvc
            interface: interface for server to listen on, 0.0.0.0 for all.
            port: service port
            handler: GServiceHandler handler instance
            mongrel2_sender_id: unique mongrel2 sender id (must be unique)
            mongrel2_pull_addr: zeromq style pull address
            mongrel2_pub_addr: zeromq style pub address
            processor: Thrift service processor
            transport: optional Thrift transport class
            transport_factory: optional Thrift transport factory
            protocol_factory: optional Thrift protocol factory
        """

        super(GMongrel2Service, self).__init__(name, interface, port, handler, processor,
                transport, transport_factory, protocol_factory)

        self.mongrel2_sender_id = mongrel2_sender_id
        self.mongrel2_pull_addr = mongrel2_pull_addr
        self.mongrel2_pub_addr = mongrel2_pub_addr
        self.mongrel2_greenlet = None

    def start(self):
        """Start service."""
        if not self.running:
            super(GMongrel2Service, self).start()
            self.mongrel2_greenlet = gevent.spawn(self.run_mongrel2)
    
    def stop(self):
        """Stop service."""
        if self.running:
            if self.mongrel2_greenlet:
                self.mongrel2_greenlet.kill()
            super(GMongrel2Service, self).stop()

    def join(self, timeout=None):
        """Join service."""
        if self.mongrel2_greenlet:
            greenlets = [self.mongrel2_greenlet, super(GMongrel2Service, self)]
            join(greenlets, timeout)
        else:
            super(GMongrel2Service, self).join(timeout)
    
    def run_mongrel2(self):
        connection = GConnection(
                self.mongrel2_sender_id,
                self.mongrel2_pull_addr,
                self.mongrel2_pub_addr)

        while self.running:
            try:
                request = connection.recv()
                gevent.spawn(self.handler.handle, connection, request)
            
            except Exception as error:
                logging.exception(error)

            except gevent.GreenletExit:
                break
