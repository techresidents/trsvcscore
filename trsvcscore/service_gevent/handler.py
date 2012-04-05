import logging

from tridlcore.gen import TRService
from tridlcore.gen.ttypes import ServiceStatus

from trpycore.mongrel2_common.request import SafeRequest
from trpycore.zookeeper_gevent.client import GZookeeperClient
from trsvcscore.http.error import HttpError
from trsvcscore.registrar.zookeeper import ZookeeperServiceRegistrar


class GServiceHandler(TRService.Iface, object):
    """Base class for service haandler"""

    def __init__(self, name, interface, port, version, build, zookeeper_hosts):
        self.name = name
        self.interface = interface
        self.port = port
        self.version = version
        self.build = build
        self.options = {}
        self.counters = {}
        self.running = False

        #Zookeeper client
        self.zookeeper_client = GZookeeperClient(zookeeper_hosts)

        #Registrar
        self.registrar = ZookeeperServiceRegistrar(self.zookeeper_client)
        
        #service will be injected by service prior to start()
        self.service = None
    
    def start(self):
        if not self.running:
            self.running = True
            self.zookeeper_client.start()
            self.registrar.register_service(self.name, self.port)
    
    def join(self):
        self.zookeeper_client.join()
    
    def stop(self):
        if self.running:
            self.running = False
            self.zookeeper_client.stop()

    def getName(self, requestContext):
        return self.name

    def getVersion(self, requestContext):
        return self.version or "Unkown"

    def getBuildNumber(self, requestContext):
        return self.build or "Unknown"

    def getStatus(self, requestContext):
        if self.running:
            return ServiceStatus.ALIVE
        else:
            return ServiceStatus.DEAD

    def getStatusDetails(self, requestContext):
        if self.running:
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


class GMongrel2Handler(GServiceHandler):
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
        super(GMongrel2Handler, self).__init__(*args, **kwargs)
    
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
            if isinstance(response, basestring):
                connection.reply_http(unsafe_request, response)
            else:
                connection.reply_http(unsafe_request, response[1], code=response[0])
        
        except HttpError as error:
            connection.reply_http(unsafe_request, error.response, code=error.http_code)

        except AttributeError as error:
            logging.exception(error)
            connection.reply_http(unsafe_request, "not found", code=404)
        
        except Exception as error:
            logging.exception(error)
            connection.reply_http(unsafe_request, "internal error", code=503)
