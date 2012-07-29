from trpycore.thread.util import join
from trsvcscore.service.base import Service

class DefaultService(Service):
    def __init__(self, name, version, build, servers):
        self.name = name
        self.version = version
        self.build = build
        self.servers = servers
        self.running = False
    
    def start(self):
        if not self.running:
            self.running = True
            for server in self.servers:
                server.start()

    def stop(self):
        if self.running:
            self.running = False
            for server in self.servers:
                server.stop()

    def join(self, timeout=None):
        join(self.servers, timeout)

    def status(self):
        result = None
        for server in self.servers:
            status = server.status()
            if result is None:
                result = status
            elif status > result:
                result = status
        return result

    def info(self):
        server_info = []
        for server in self.servers:
            server_info.append(server.info())
