import logging

from tridlcore.gen import TRService
from tridlcore.gen.ttypes import ServiceStatus

from trpycore.mongrel2_common.request import SafeRequest
from trpycore.zookeeper_gevent.client import GZookeeperClient
from trsvcscore.http.error import HttpError
from trsvcscore.registrar.zookeeper import ZookeeperServiceRegistrar


class GServiceHandler(TRService.Iface, object):
    """Base class for gevent service handler."""

    def __init__(self, name, interface, port, version, build, zookeeper_hosts):
        """GServiceHandler constructor.

        Args:
            name: service name, i.e. chatsvc
            interface: interface service is listening on, 0.0.0.0 for all.
            port: service port
            version: service version (string)
            build: service build number (string)
            zookeeper_hosts: list of zookeeper hosts, i.e. ["localhost:2181", "localdev:2181"]
        """
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
        """Start service handler."""
        if not self.running:
            self.running = True
            self.zookeeper_client.start()
            self.registrar.register_service(self.name, self.port)
    
    def join(self):
        """Join service handler."""
        self.zookeeper_client.join()
    
    def stop(self):
        """Stop service handler."""
        if self.running:
            self.running = False
            self.zookeeper_client.stop()

    def getName(self, requestContext):
        """Get service name.

        Args:
            requestContext: RequestContext object containing user information.
        
        Returns:
            service name (string)
        """
        return self.name

    def getVersion(self, requestContext):
        """Get service version.

        Args:
            requestContext: RequestContext object containing user information.
        
        Returns:
            service version (string)
        """
        return self.version or "Unkown"

    def getBuildNumber(self, requestContext):
        """Get service build number.

        Args:
            requestContext: RequestContext object containing user information.
        
        Returns:
            service build number (string)
        """
        return self.build or "Unknown"

    def getStatus(self, requestContext):
        """Get service status.

        Args:
            requestContext: RequestContext object containing user information.
        
        Returns:
            ServiceStatus constant
        """
        if self.running:
            return ServiceStatus.ALIVE
        else:
            return ServiceStatus.DEAD

    def getStatusDetails(self, requestContext):
        """Get service status details.

        Args:
            requestContext: RequestContext object containing user information.
        
        Returns:
            String description of the current ServiceStatus constant.
        """
        if self.running:
            return "Alive and well"
        else:
            return "Dead"

    def getCounters(self, requestContext):
        """Get service counters.

        Args:
            requestContext: RequestContext object containing user information.
        
        Returns:
            Dict of service specific counters.
        """
        return self.counters

    def getOption(self, requestContext, key):
        """Get service option.

        Args:
            requestContext: RequestContext object containing user information.
            key: Option name
        
        Returns:
            String value for the option.
        """
        return self.options[key]

    def getOptions(self, requestContext):
        """Get all service options.

        Args:
            requestContext: RequestContext object containing user information.
        
        Returns:
            Dict of service specific options  key / values.
        """
        return self.options

    def setOption(self, requestContext, key, value):
        """Set service options.

        Args:
            requestContext: RequestContext object containing user information.
            key: Option name (string)
            value: Option value
        """
        self.options[key] = value

    def shutdown(self, requestContext):
        """Shutdown service.

        Args:
            requestContext: RequestContext object containing user information.
        """
        self.service.stop()

    def reinitialize(self, requestContext):
        """Reinitialize service.

        Args:
            requestContext: RequestContext object containing user information.
        """
        pass


class GMongrel2Handler(GServiceHandler):
    """Base class for Mongrel2 service handler.
       
     Incoming http requests will be delegated to a method named as follows:

        handle_<method>_<url_with_slashes_replaced_by_underscores>
        
        where method is "get", "post", etc.. and <url...> is the full
        url with the slashes replaced by underscores.

    For example a POST to www.server.com/myapp/chat will invoke
    the "handle_post_myapp_chat" method with a SafeRequest as 
    the sole parameter.
    """

    def __init__(self, *args, **kwargs):
        """GMongrel2Handler constructor.

        Arguments are identical to GServiceHandler.
        """
        super(GMongrel2Handler, self).__init__(*args, **kwargs)
    
    def handle(self, connection, unsafe_request):
        """Method will be invoked when a Mongrel2 request is received.

        Incoming http requests will be delegated to a method named as follows:

           handle_<method>_<url_with_slashes_replaced_by_underscores>
           
           where method is "get", "post", etc.. and <url...> is the full
           url with the slashes replaced by underscores.

        For example a POST to www.server.com/myapp/chat will invoke
        the "handle_post_myapp_chat" method with a SafeRequest as 
        the sole parameter.

        Delegated methods may return the http response (string),
        or a (http_code, response) tuple, or
        raise an HttpError exception to signal an error.
        """

        request = SafeRequest(unsafe_request)
        
        #If client disconnected invoke handle_disconnect()
        if unsafe_request.is_disconnect():
            try:
                self.handle_disconnect(request)
            except Exception as error:
                logging.exception(error)
            return

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
    
    def handle_disconnect(self, request):
        """Disconnection handler to be overriden by subclass."""
        pass
