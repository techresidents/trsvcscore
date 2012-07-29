import logging

import gevent

from tridlcore.gen.ttypes import ServiceStatus
from trpycore.mongrel2_gevent.handler import GConnection
from trsvcscore.service.server.base import Server, ServerInfo

class GMongrel2Server(Server):
    """Base class for gevent Mongrel2 services."""

    def __init__(self, mongrel2_sender_id,
            mongrel2_pull_addr, mongrel2_pub_addr, handler):
        """GMongrel2Service constructor.
        Args:
            mongrel2_sender_id: unique mongrel2 sender id (must be unique)
            mongrel2_pull_addr: zeromq style pull address
            mongrel2_pub_addr: zeromq style pub address
            handler: GServiceHandler handler instance
        """

        self.mongrel2_sender_id = mongrel2_sender_id
        self.mongrel2_pull_addr = mongrel2_pull_addr
        self.mongrel2_pub_addr = mongrel2_pub_addr
        self.handler = handler
        self.running = False
        self._status = ServiceStatus.STOPPED
        self.greenlet = None

    def start(self):
        """Start service."""
        if not self.running:
            self.running = True
            self._status = ServiceStatus.STARTING
            self.greenlet = gevent.spawn(self.run)
    
    def stop(self):
        """Stop service."""
        if self.running:
            self.running = False
            self._status = ServiceStatus.STOPPING
            if self.greenlet:
                self.greenlet.kill()

    def join(self, timeout=None):
        """Join service."""
        if self.greenlet:
            self.greenlet.join(timeout)
    
    def run(self):
        self._status = ServiceStatus.ALIVE

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
                self._status = ServiceStatus.STOPPED
                break

        self._status = ServiceStatus.STOPPED

    def status(self):
        return self._status

    def info(self):
        endpoints = []
        return ServerInfo(endpoints)
