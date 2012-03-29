#!/usr/bin/env python

from tridlcore.gen import TRService
from tridlcore.gen.ttypes import ServiceStatus

class ServiceHandler(TRService.Iface, object):
    """Base class for service haandler"""

    def __init__(self, name, version, build):
        self.name = name,
        self.version = version
        self.build = build
        self.options = {}
        self.counters = {}
        self.service = None
    
    def getName(self, requestContext):
        return self.name

    def getVersion(self, requestContext):
        return self.version or "Unkown"

    def getBuildNumber(self, requestContext):
        return self.build or "Unknown"

    def getStatus(self, requestContext):
        if self.service and self.service.running:
            return ServiceStatus.ALIVE
        else:
            return ServiceStatus.DEAD

    def getStatusDetails(self, requestContext):
        if self.service and self.service.running:
            return "Alive and well"
        else:
            return "Dead"

    def getCounters(self, requestContext):
        return self.counters

    def getOption(self, requestContext, key):
        return self.options[key]

    def getOptions(self, requestContext):
        return self.options

    def setOption(self, requestContext, key, value):
        self.options[key] = value

    def shutdown(self, requestContext):
        self.service.stop()

    def reinitialize(self, requestContext):
        pass

class Mongrel2Handler(ServiceHandler):
    """Base class for Mongrel2 service handler"""
    def __init__(self, *args, **kwargs):
        super(Mongrel2Handler, self).__init__(*args, **kwargs)
    
    def handle(self, connection, request):
        pass
