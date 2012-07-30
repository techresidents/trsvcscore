import logging
import re

from gevent.event import Event

from tridlcore.gen.ttypes import Status

from trpycore.mongrel2_common.request import SafeRequest
from trsvcscore.http.error import HttpError
from trsvcscore.service.handler.base import Handler

class GMongrel2Handler(Handler):
    """Gevent Mongrel2 handler.
       
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


    def __init__(self, url_handlers=None):
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
        self.url_handlers = []
        self.running = False
        self.stop_event = Event()

        #Compile url regular expressions
        for url_regex, handler_name in url_handlers or []:
            self.url_handlers.append((re.compile(url_regex), handler_name))

    
    def start(self):
        """Start handler."""
        if not self.running:
            self.running = True
            self.stop_event.clear()

    def stop(self):
        """Stop handler."""
        if self.running:
            self.running = False
            self.stop_event.set()

    def join(self, timeout=None):
        """Join the handler.

        Join the handler, waiting for the completion of all threads 
        or greenlets.

        Args:
            timeout: Optional timeout in seconds to observe before returning.
                If timeout is specified, the status() method must be called
                to determine if the handler is still running.
        """
        while self.running:
            self.stop_event.wait(timeout)
            if timeout is not None:
                break

    def status(self):
        """Get the handler status.

        Returns Status enum.
        """
        if self.running:
            return Status.ALIVE
        else:
            return Status.STOPPED

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
