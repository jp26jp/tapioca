class ResponseProcessException(Exception):
    def __init__(self, tapioca_exception, data, *args, **kwargs):
        self.tapioca_exception = tapioca_exception
        self.data = data
        super().__init__(*args, **kwargs)


class TapiocaException(Exception):
    def __init__(self, message, client):
        self.status_code = None
        self.client = client
        if client is not None:
            self.status_code = client().status_code

        if not message:
            message = f"response status code: {self.status_code}"
        super().__init__(message)


class ClientError(TapiocaException):
    def __init__(self, message="", client=None):
        super().__init__(message, client=client)


class NotFoundError(ClientError):
    def __init__(self, message="", client=None):
        super().__init__(message, client=client)


class BadRequest(TapiocaException):
    def __init__(self, message="", client=None):
        super().__init__(message, client=client)


class RateLimit(TapiocaException):
    def __init__(self, message="", client=None):
        super().__init__(message, client=client)


class InvalidCredentials(TapiocaException):
    def __init__(self, message="", client=None):
        super().__init__(message, client=client)


class AccessDenied(TapiocaException):
    def __init__(self, message="", client=None):
        super().__init__(message, client=client)


class ServerError(TapiocaException):
    def __init__(self, message="", client=None):
        super().__init__(message, client=client)


def exception_handler(function):
    def _(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except AccessDenied:
            print("Access denied", args, kwargs)
        except BadRequest:
            print(args[0])
            print("Bad request or invalid data sent", args, kwargs)

    return _
