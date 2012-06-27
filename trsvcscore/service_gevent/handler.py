import logging
import re

from tridlcore.gen import TRService
from tridlcore.gen.ttypes import ServiceStatus

from trpycore.mongrel2_common.request import SafeRequest
from trpycore.zookeeper_gevent.client import GZookeeperClient
from trsvcscore.http.error import HttpError
from trsvcscore.registrar.zookeeper import ZookeeperServiceRegistrar


class GServiceHandler(TRService.Iface, object):
    """Base class for gevent service handler."""

    def __init__(self, name, interface, port, version, build, zookeeper_hosts, database_connection=None):
        """GServiceHandler constructor.

        Args:
            name: service name, i.e. chatsvc
            interface: interface service is listening on, 0.0.0.0 for all.
            port: service port
            version: service version (string)
            build: service build number (string)
            zookeeper_hosts: list of zookeeper hosts, i.e. ["localhost:2181", "localdev:2181"]
            database_connection: optional database connection string
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

        #Database session factory
        if database_connection:
            #Make psycogp2 driver compatible with gevent
            from trpycore import psycopg2_gevent
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            engine = create_engine(database_connection)
            self.DatabaseSession = sessionmaker(bind=engine)
        else:
            self.DatabaseSession = None

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

    def get_database_session(self):
        """Return new database SQLAlchemy database session.

        Returns:
            new SQLAlchemy session
        Raises:
            RuntimeError: If database_connection not provided to handler.
        """
        if self.DatabaseSession:
            return self.DatabaseSession()
        else:
            raise RuntimeError("database_connection not provided")

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
        return self.version or "Unknown"

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
       
     Incoming http requests will be delegated to method handlers
     based on a list of url_handlers. Each list entry will
     be a (url_regex_pattern, handler_method_name) tuple.

     In order to find the appropriate handler method, the
     absolute request url will be compared against each
     list entry's url_regex until a match is found. 

     If a match is the found the handler_method_name will
     be resolved via getattr and the method will be
     invoked with a SafeRequest object, and additional
     keyword arguments determined by the url_regex
     group name captures.

     Example:
         (r'/lookup/(?P<category>\w+$', 'handle_lookup')

         For a  GET to  URL /lookup/technology would result in
         self.handle_lookup(request, category='technology')
         method invocation.
    
    If a match is not found, a 404 error will be returned to
    the client.
    """

    class Response(object):
        """Mongrel2 response object.

        This object should be returned from url handlers.
        """
        def __init__(self, data=None, code=200, headers=None):
            self.data = data 
            self.code = code
            self.headers = headers or {}
    
    class JsonResponse(Response):
        """Mongrel2 JSON response."""
        def __init__(self, *args, **kwargs):
            super(GMongrel2Handler.JsonResponse, self).__init__(*args, **kwargs)
            self.headers["content-type"] = "application/json"


    def __init__(self, url_handlers=None, *args, **kwargs):
        """GMongrel2Handler constructor.
        
        Args:
            url_handlers: List of (url_regex_pattern, handler_method_name)  
                tuples. The absolute request url will be 
                compared against each list entry's url_regex
                until a match is found. 

                If a match is the found the handler_method_name will
                be resolved via getattr and the method will be
                invoked with a SafeRequest object, and additional
                keyword arguments determined by the url_regex
                group name captures.

                Example:
                    (r'/lookup/(?P<category>\w+$', 'handle_lookup')

                    For a  GET to  URL /lookup/technology would result in
                    self.handle_lookup(request, category='technology')
                    method invocation.
                
                If a match is not found a 404 error will returned 
                to the client.

            Additional arguments are identical to GServiceHandler.
        """
        super(GMongrel2Handler, self).__init__(*args, **kwargs)
        self.url_handlers = []

        #Compile url regular expressions
        for url_regex, handler_name in url_handlers or []:
            self.url_handlers.append((re.compile(url_regex), handler_name))
    
    def handle(self, connection, unsafe_request):
        """Method will be invoked when a Mongrel2 request is received.

        Incoming http requests will be delegated to a method named as follows:

           handle_<method>_<url_with_slashes_replaced_by_underscores>
           
           where method is "get", "post", etc.. and <url...> is the full
           url with the slashes replaced by underscores.

        For example a POST to www.server.com/myapp/chat will invoke
        the "handle_post_myapp_chat" method with a SafeRequest as 
        the sole parameter.

        Delegated methods may return a Response object
        or raise an HttpError exception to signal an error.
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

        try:
            match = None

            #Find the handler for the incoming request
            for url_regex, handler_name in self.url_handlers:
                match = url_regex.match(url)
                if match:
                    break
            
            if match is None:
                raise HttpError(404, "not found")
            
            #Process the request
            handler = getattr(self, handler_name)
            response = handler(request, **match.groupdict())
            connection.reply_http(
                    unsafe_request,
                    body=response.data,
                    code=response.code,
                    headers=response.headers)
        
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
