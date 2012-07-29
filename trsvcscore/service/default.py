from trpycore.thread.util import join
from trsvcscore.service.base import Service, ServiceInfo

class DefaultService(Service):
    def __init__(self, name, version, build, hostname, fqdn, servers):
        self._name = name
        self._version = version
        self._build = build
        self.hostname = hostname
        self.fqdn = fqdn
        self.servers = servers
        self.running = False
    
    def name(self):
        return self._name

    def version(self):
        return self._version

    def build(self):
        return self._build

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
        
        result = ServiceInfo(
                self._name,
                self._version,
                self._build,
                self.hostname,
                self.fqdn,
                server_info)

        return result
