from trsvcscore.http.error import HttpError

def session_required(func):
    """@session_required decorator.

    Checks to see if the incoming Mongrel2 request was sent with a valid sessionid cookie.
    This decorator needs a SessionStore pool object available in self.session_store_pool to run.
    If the session is valid the decorated method will be invoked with an additional
    session argument, immediately following the request paramater, containing the validate session.
    All additoinal keyword arguments will follow the session argument.

    Raises:
        HTTPError if valid session is not found.
    """

    def check(self, request, **kwargs):
        with self.session_store_pool.get() as session_store:
            session = session_store.get_session(request.cookie("sessionid"))
            if not session:
                raise HttpError(401, "access denied")
            else:
                return func(self, request, session, **kwargs)
    return check
