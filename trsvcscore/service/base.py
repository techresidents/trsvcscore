import abc
import json

from trsvcscore.service.server.base import ServerInfo

class ServiceInfo(object):
    def __init__(self, name, version, build, hostname, fqdn, servers):
        self.name = name
        self.version = version
        self.build = build
        self.hostname = hostname
        self.fqdn = fqdn
        self.servers = servers

    @staticmethod
    def from_json(data):
        if isinstance(data, basestring):
            json_dict = json.loads(data)
        else:
            json_dict = data

        servers = [ServerInfo.from_json(s) for s in json_dict["servers"]]

        result = ServiceInfo(
                json_dict["name"],
                json_dict["version"],
                json_dict["build"],
                json_dict["hostname"],
                json_dict["fqdn"],
                servers)

        return result

    def to_json(self):
        json_servers = [s.to_json() for s in self.servers]
        return {
            "name": self.name,
            "version": self.version,
            "build": self.build,
            "hostname": self.hostname,
            "fqdn": self.fqdn,
            "servers": json_servers
        }

class Service(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def name(self):
        return

    @abc.abstractmethod
    def version(self):
        return

    @abc.abstractmethod
    def build(self):
        return
   

    @abc.abstractmethod
    def start(self):
        return

    @abc.abstractmethod
    def stop(self):
        return

    @abc.abstractmethod
    def join(self, timeout=None):
        return

    @abc.abstractmethod
    def status(self):
        return

    @abc.abstractmethod
    def info(self):
        return
