import logging
import socket

import gevent

from thrift import Thrift
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

from tridlcore.gen.ttypes import ServiceStatus
from trpycore.greenlet.util import join
from trpycore.thrift_gevent.server import TGeventServer
from trpycore.thrift_gevent.transport import TSocket
from trsvcscore.service.server.base import Server, ServerInfo, ServerEndpoint, ServerProtocol, ServerTransport

class GThriftServer(Server):
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
        self._status = ServiceStatus.STOPPED
    
    def start(self):
        """Start service."""
        if not self.running:
            self._status = ServiceStatus.STARTING
            self.running = True
            self.greenlet = gevent.spawn(self.run)
            self.handler.start()
    
    def run(self):
        self._status = ServiceStatus.ALIVE
        
        errors = 0

        while self.running:
            try:
                server = TGeventServer(self.processor, self.transport, self.transport_factory, self.protocol_factory)
                server.serve()

            except Exception as error:
                logging.exception(error)
                
                errors += 1
                if errors >= 10:
                    logging.error("Halting service (errors >= %s)" % errors)
                    self._status = ServiceStatus.DEAD

            except gevent.GreenletExit:
                break
        
        #Set status to STOPPED if it's not DEAD
        if self._status != ServiceStatus.DEAD:
            self._status = ServiceStatus.STOPPED
    
    def stop(self):
        """Stop service."""
        if self.running:
            self._status = ServiceStatus.STOPPING
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
    
    def status(self):
        return self._status

    def info(self):
        endpoint = ServerEndpoint(
                address=socket.gethostname(),
                port=self.port,
                protocol=ServerProtocol.THRIFT,
                transport=ServerTransport.TCP)
        
        return ServerInfo([endpoint])
