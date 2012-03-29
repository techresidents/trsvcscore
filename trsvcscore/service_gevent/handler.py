#!/usr/bin/env python

import logging

from trpycore.mongrel2_common.request import SafeRequest

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
    """Base class for Mongrel2 service handler
       
       Incoming http requests will be delegated to a method named as follows:

          handle_<method>_<url_with_slashes_replaced_by_underscores>
          
          where method is "get", "post", etc.. and <url...> is the full
          url with the slashes replaced by underscores.

      For example a POST to www.server.com/myapp/chat will invoke
      the "handle_post_myapp_chat" method with a SafeRequest as 
      the sole parameter.
    """

    def __init__(self, *args, **kwargs):
        super(Mongrel2Handler, self).__init__(*args, **kwargs)
    
    def handle(self, connection, unsafe_request):
        if unsafe_request.is_disconnect():
            return

        request = SafeRequest(unsafe_request)
        url = request.header("PATH")
        method = request.method()

        try:
            handler_name = "handle_%s%s" % (method, url.replace("/", "_"))
            handler = getattr(self, handler_name.lower())
            response = handler(request)
            connection.reply_http(unsafe_request, response)

        except AttributeError as error:
            logging.exception(error)
            connection.reply_http(unsafe_request, "not found", code=404)
        
        except Exception as error:
            logging.exception(error)
            connection.reply_http(unsafe_request, "internal error", code=503)
