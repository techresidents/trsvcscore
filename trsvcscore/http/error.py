class HttpError(Exception):
    """General exception for Http errors."""
    def __init__(self, http_code, response):
        self.http_code = http_code
        self.response = response
