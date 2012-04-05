import logging
import gevent

from thrift import Thrift
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

from trpycore.thrift_gevent.server import TGeventServer
from trpycore.thrift_gevent.transport import TSocket
from trpycore.mongrel2_gevent.handler import GConnection

class GService(object):
    """Base class for gevent services"""
    def __init__(self, name, interface, port, handler, processor,
            transport=None, transport_factory=None, protocol_factory=None):
        
        self.name = name
        self.interface = interface
        self.port = port
        self.handler = handler
        self.processor = processor
        self.transport = transport or TSocket.TServerSocket(self.interface, self.port)
        self.transport_factory = transport_factory or TTransport.TBufferedTransportFactory()
        self.protocol_factory = protocol_factory or TBinaryProtocol.TBinaryProtocolFactory()
        self.greenlets = []
        self.running = False
        
        self.handler.service = self
    
    def start(self):
        if not self.running:
            self.running = True
            self.greenlets.append(gevent.spawn(self.run))
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
        if self.running:
            self.running = False
            self.handler.stop()
            for greenlet in self.greenlets:
                greenlet.kill()

            self.greenlets = []
    
    def join(self):
        self.handler.join()
        for greenlet in self.greenlets:
            greenlet.join()


class GMongrel2Service(GService):
    """Base class for gevent Mongrel2 services"""

    def __init__(self, name,  interface, port, processor, handler,
            mongrel2_sender_id, mongrel2_pull_addr, mongrel2_pub_addr,
            transport=None, transport_factory=None, protocol_factory=None):

        super(GMongrel2Service, self).__init__(name, interface, port, handler, processor,
                transport, transport_factory, protocol_factory)

        self.mongrel2_sender_id = mongrel2_sender_id
        self.mongrel2_pull_addr = mongrel2_pull_addr
        self.mongrel2_pub_addr = mongrel2_pub_addr
        self.mongrel2_greenlet = None

    def start(self):
        if not self.running:
            super(GMongrel2Service, self).start()
            self.greenlets.append(gevent.spawn(self.run_mongrel2))
    
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
