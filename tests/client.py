# coding: utf-8

from __future__ import unicode_literals

from tapioca.adapters import (
    TapiocaAdapter, JSONAdapterMixin,
    generate_wrapper_from_adapter)
from tapioca.serializers import SimpleSerializer


RESOURCE_MAPPING = {
    'test': {
        'resource': 'test/',
        'docs': 'http://www.example.org'
    },
    'user': {
        'resource': 'user/{id}/',
        'docs': 'http://www.example.org/user'
    },
    'resource': {
        'resource': 'resource/{number}/',
        'docs': 'http://www.example.org/resource',
        'spam': 'eggs',
        'foo': 'bar'
    },
    'another_root': {
        'resource': 'another-root/',
        'docs': 'http://www.example.org/another-root'
    },
}


class TesterClientAdapter(JSONAdapterMixin, TapiocaAdapter):
    serializer_class = None
    api_root = 'https://api.example.org'
    resource_mapping = RESOURCE_MAPPING

    def get_api_root(self, api_params, **kwargs):
        if kwargs.get('resource_name') == 'another_root':
            return 'https://api.another.com/'
        else:
            return self.api_root

    def get_iterator_list(self, response_data):
        return response_data['data']

    def get_iterator_next_request_kwargs(self, iterator_request_kwargs,
                                         response_data, response):
        paging = response_data.get('paging')
        if not paging:
            return
        url = paging.get('next')

        if url:
            return {'url': url}


TesterClient = generate_wrapper_from_adapter(TesterClientAdapter)


class CustomSerializer(SimpleSerializer):

    def to_kwargs(self, data, **kwargs):
        return kwargs


class SerializerClientAdapter(TesterClientAdapter):
    serializer_class = CustomSerializer


SerializerClient = generate_wrapper_from_adapter(SerializerClientAdapter)


class TokenRefreshClientAdapter(TesterClientAdapter):

    def is_authentication_expired(self, exception, *args, **kwargs):
        return exception.status_code == 401

    def refresh_authentication(self, api_params, *args, **kwargs):
        new_token = 'new_token'
        api_params['token'] = new_token
        return new_token


TokenRefreshClient = generate_wrapper_from_adapter(TokenRefreshClientAdapter)


class FailTokenRefreshClientAdapter(TokenRefreshClientAdapter):

    def refresh_authentication(self, api_params, *args, **kwargs):
        return None


FailTokenRefreshClient = generate_wrapper_from_adapter(FailTokenRefreshClientAdapter)


