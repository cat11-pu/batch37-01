class CorsPolicy:
    def __init__(self, allowed_origins, allow_credentials=False):
        self.allowed_origins = allowed_origins
        self.allow_credentials = allow_credentials

    def headers(self, origin, method, request_headers=None):
        return {}
