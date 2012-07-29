import logging
import socket
import threading

from thrift.transport import TTransport, TSocket
from thrift.protocol import TBinaryProtocol

from tridlcore.gen.ttypes import ServiceStatus
from trpycore.thrift.server import TThreadPoolServer
from trpycore.thread.util import join
from trsvcscore.service.server.base import Server, ServerInfo, ServerEndpoint, ServerProtocol, ServerTransport

class ThriftServer(Server):
    """Base class for services"""
    def __init__(self, name, interface, port, handler, processor, threads=5,
            transport=None, transport_factory=None, protocol_factory=None):
        """Service constructor.

        Args:
            name: service name, i.e. chatsvc
            interface: interface for server to listen on, 0.0.0.0 for all.
            port: service port
            handler: ServiceHandler handler instance
            processor: Thrift service processor
            threads: Number of worker threads to allocate.
                Each thread will handle one and only one client connection
                at a time, so set this accordingly. In the future this
                should be enhanced to use a transport which  multiplex connections,
                and dispatches requests (not connections) to workers.
            transport: optional Thrift transport class
            transport_factory: optional Thrift transport factory
            protocol_factory: optional Thrift protocol factory
        """
        super(ThriftServer, self).__init__()
        
        self.name = name
        self.interface = interface
        self.port = port
        self.handler = handler
        self.processor = processor
        self.threads = threads
        self.transport = transport or TSocket.TServerSocket(self.interface, self.port)
        self.transport_factory = transport_factory or TTransport.TBufferedTransportFactory()
        self.protocol_factory = protocol_factory or TBinaryProtocol.TBinaryProtocolFactory()
        self.running = False
        self.server = None
        self._status = ServiceStatus.STOPPED

        self.thread = threading.Thread(target=self.run)
    
    def _run_server(self):
        """Run thrift server.
        This method needs be invoked in a separate thread.
        TThreadPoolServer.serve() blocks forever in an 
        uninterruptible manner, so it needs to be invoked
        in a daemon thread which will not prevent the 
        service process from exiting.
        """

        errors = 0
        while self.running:
            try:
                #TODO replace TThreadPoolServer with a transport which
                #multiplexes connections and dispatches requests
                #(not connections) to workers.
                self.server = TThreadPoolServer(
                        self.processor,
                        self.transport,
                        self.transport_factory,
                        self.protocol_factory,
                        daemon=True)
                self.server.setNumThreads(self.threads)
                self.server.serve()

            except Exception as error:
                logging.exception(error)

                errors += 1
                if errors >= 10:
                    self._status = ServiceStatus.DEAD
                    logging.error("Halting server (errors >=  %s)" % error)
                    break

    def start(self):
        """Start server."""
        if not self.running:
            self._status = ServiceStatus.STARTING
            self.running = True
            self.handler.start()
            self.thread.start()
    
    def run(self):
        """Run server."""
        #Start thrift server in separate daemon thread
        #to allow service process to properly exit
        #following service.stop()
        thread = threading.Thread(target=self._run_server)
        thread.daemon = True
        thread.start()
        
        self._status = ServiceStatus.ALIVE

        #Wait for stop
        while self.running:
            try:
                thread.join(1)

            except Exception as error:
                logging.exception(error)
        
        #Set service status to STOPPED as long as it's not DEAD
        if self._status != ServiceStatus.DEAD:
            self._status = ServiceStatus.STOPPED

    def join(self, timeout=None):
        join([self.handler, self.thread], timeout)

    def stop(self):
        """Stop server."""
        if self.running:
            self._status = ServiceStatus.STOPPING
            self.running = False
            self.handler.stop()

            #Note that server.stop() does not guarantee
            #that worker threads will exit in timely 
            #manner. Additionally, it will not unblock
            #server.serve().
            self.server.stop()

    def status(self):
        return self._status

    def info(self):
        endpoint = ServerEndpoint(
                address=socket.gethostname(),
                port=self.port,
                protocol=ServerProtocol.THRIFT,
                transport=ServerTransport.TCP)
        
        return ServerInfo([endpoint])
