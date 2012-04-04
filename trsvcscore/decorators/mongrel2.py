from trsvcscore.http.error import HttpError

def session_required(func):
    def check(self, request):
        session = self.session_store.get_session(request.cookie("sessionid"))
        if not session:
            raise HttpError(401, "access denied")
        else:
            return func(self, request, session)
    return check
