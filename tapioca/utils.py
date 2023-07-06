import requests.auth


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = f"Bearer {self.token}"
        return r


class CustomAuth(requests.auth.AuthBase):
    def __init__(self, key_name, key_value):
        self.key_name = key_name
        self.key_value = key_value

    def __call__(self, r):
        r.headers[self.key_name] = self.key_value
        return r
