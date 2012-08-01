import logging
import socket

import gevent

from thrift import Thrift
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

from tridlcore.gen.ttypes import Status
from trpycore.greenlet.util import join
from trpycore.thrift_gevent.server import TGeventServer
from trpycore.thrift_gevent.transport import TSocket
from trsvcscore.service.server.base import Server, ServerInfo, ServerEndpoint, ServerProtocol, ServerTransport

class GThriftServer(Server):
    """Gevent Thrift Server."""
    def __init__(self, name, interface, port, handler, processor, address=None,
            transport=None, transport_factory=None, protocol_factory=None):
        """GThriftServer constructor.

        Args:
            name: server name, i.e. chatsvc-thrift
            interface: interface for server to listen on, 0.0.0.0 for all.
            port: service port
            handler: GServiceHandler handler instance
            processor: Thrift service processor
            address: optional address to advertise in ServerInfo.
                This may be a hostname, fqdn, or ip address. If no
                address is provided, socket.gethostname() will
                be used.
            transport: optional Thrift server transport object
            transport_factory: optional Thrift transport factory
            protocol_factory: optional Thrift protocol factory
        """
        
        self.name = name
        self.interface = interface
        self.port = port
        self.handler = handler
        self.processor = processor
        self.address = address or socket.gethostname()
        self.transport = transport or TSocket.TServerSocket(self.interface, self.port)
        self.transport_factory = transport_factory or TTransport.TBufferedTransportFactory()
        self.protocol_factory = protocol_factory or TBinaryProtocol.TBinaryProtocolFactory()
        self.greenlet = None
        self.running = False
        self._status = Status.STOPPED
    
    def start(self):
        """Start server."""
        if not self.running:
            self._status = Status.STARTING
            self.running = True
            self.greenlet = gevent.spawn(self.run)
            self.handler.start()
    
    def run(self):
        """Run server."""
        self._status = Status.ALIVE
        
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
                    self._status = Status.DEAD

            except gevent.GreenletExit:
                break
        
        #Set status to STOPPED if it's not DEAD
        if self._status != Status.DEAD:
            self._status = Status.STOPPED
    
    def stop(self):
        """Stop server."""
        if self.running:
            self._status = Status.STOPPING
            self.running = False
            self.handler.stop()
            self.greenlet.kill()
    
    def join(self, timeout=None):
        """Join server.

        Join the server, waiting for the completion of all threads 
        or greenlets.

        Args:
            timeout: Optional timeout in seconds to observe before returning.
                If timeout is specified, the status() method must be called
                to determine if the service is still running.
        """
        join([self.handler, self.greenlet], timeout)
    
    def status(self):
        """Get server status.

        Returns:
            Status enum.
        """
        return self._status

    def info(self):
        """Get server info.

        Returns:
            ServerInfo object.
        """
        endpoint = ServerEndpoint(
                address=self.address,
                port=self.port,
                protocol=ServerProtocol.THRIFT,
                transport=ServerTransport.TCP)
        
        return ServerInfo(self.name, [endpoint])
