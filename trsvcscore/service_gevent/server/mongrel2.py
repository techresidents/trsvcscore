import logging

import gevent

from tridlcore.gen.ttypes import Status
from trpycore.mongrel2_gevent.handler import GConnection
from trsvcscore.service.server.base import Server, ServerInfo

class GMongrel2Server(Server):
    """Greenlet Mongrel2 server."""

    def __init__(self, name, mongrel2_sender_id,
            mongrel2_pull_addr, mongrel2_pub_addr, handler):
        """GMongrel2Service constructor.
        Args:
            name: server name, i.e. chatsvc-mongrel
            mongrel2_sender_id: unique mongrel2 sender id (must be unique)
            mongrel2_pull_addr: zeromq style pull address
            mongrel2_pub_addr: zeromq style pub address
            handler: GServiceHandler handler instance
        """
        self.name = name
        self.mongrel2_sender_id = mongrel2_sender_id
        self.mongrel2_pull_addr = mongrel2_pull_addr
        self.mongrel2_pub_addr = mongrel2_pub_addr
        self.handler = handler
        self.running = False
        self._status = Status.STOPPED
        self.greenlet = None

    def start(self):
        """Start server."""
        if not self.running:
            self.running = True
            self._status = Status.STARTING
            self.greenlet = gevent.spawn(self.run)
    
    def stop(self):
        """Stop server."""
        if self.running:
            self.running = False
            self._status = Status.STOPPING
            self.greenlet.kill()

    def join(self, timeout=None):
        """Join the server.

        Join the server, waiting for the completion of all threads 
        or greenlets.

        Args:
            timeout: Optional timeout in seconds to observe before returning.
                If timeout is specified, the status() method must be called
                to determine if the service is still running.
        """
        self.greenlet.join(timeout)
    
    def run(self):
        """Run server."""
        self._status = Status.ALIVE

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
                self._status = Status.STOPPED
                break

        self._status = Status.STOPPED

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
        endpoints = []
        return ServerInfo(self.name, endpoints)
