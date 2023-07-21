from __future__ import unicode_literals

import copy
import json
import time
import webbrowser
from collections import OrderedDict

import requests as requests

from .exceptions import ResponseProcessException


from typing import Type, Optional, Any

class TapiocaInstantiator:
    """
    A callable object that creates a TapiocaClient instance using the provided parameters.
    """

    def __init__(self, adapter_class: Type) -> None:
        """
        Initialize TapiocaInstantiator with the given adapter class.

        :param adapter_class: The adapter class to be used when creating the TapiocaClient.
        :type adapter_class: Type
        """
        self.adapter_class = adapter_class

    def __call__(self, serializer_class: Optional[Type] = None, session: Optional[Any] = None, **kwargs):
        """
        Create a TapiocaClient instance using the stored adapter class and the provided parameters.

        :param serializer_class: The serializer class to be used by the adapter class. Defaults to None.
        :type serializer_class: Optional[Type]
        :param session: The session to be used by the TapiocaClient. Defaults to None.
        :type session: Optional[Any]
        :param kwargs: Additional parameters to be passed to the TapiocaClient.
        :return: A TapiocaClient instance configured with the provided parameters.
        :rtype: TapiocaClient
        """
        refresh_token_default = kwargs.pop("refresh_token_by_default", False)
        return TapiocaClient(
            self.adapter_class(serializer_class=serializer_class),
            api_params=kwargs,
            refresh_token_by_default=refresh_token_default,
            session=session,
        )


class TapiocaClient(object):
    def __init__(
        self,
        api,
        data=None,
        response=None,
        request_kwargs=None,
        api_params=None,
        resource=None,
        refresh_token_by_default=False,
        refresh_data=None,
        session=None,
        *args,
        **kwargs,
    ):
        """
        Initialize a TapiocaClient instance.

        :param api: The API object.
        :type api: Any
        :param data: Data to be stored in the client object (default is None).
        :type data: Any, optional
        :param response: Response to be stored in the client object (default is None).
        :type response: Any, optional
        :param request_kwargs: Keyword arguments for request (default is None).
        :type request_kwargs: dict, optional
        :param api_params: Parameters for the API (default is {}).
        :type api_params: dict, optional
        :param resource: Resource to be stored in the client object (default is None).
        :type resource: Any, optional
        :param refresh_token_by_default: Whether to refresh the token by default (default is False).
        :type refresh_token_by_default: bool, optional
        :param refresh_data: Data to be refreshed (default is None).
        :type refresh_data: Any, optional
        :param session: Session to be used (default is a new requests.Session()).
        :type session: requests.Session, optional
        """
        self._api = api
        self._data = data
        self._response = response
        self._api_params = api_params or {}
        self._request_kwargs = request_kwargs
        self._resource = resource
        self._refresh_token_default = refresh_token_by_default
        self._refresh_data = refresh_data
        self._session = session or requests.Session()

    def _instatiate_api(self):
        """
        Instantiate the API.

        :returns: Instance of the API.
        :rtype: Any
        """
        serializer_class = None
        if self._api.serializer:
            serializer_class = self._api.serializer.__class__
        return self._api.__class__(serializer_class=serializer_class)

    def _wrap_in_tapioca(self, data, *args, **kwargs):
        """
        Wrap the data in a TapiocaClient.

        :param data: Any data to be wrapped.
        :type data: Any
        :returns: Instance of TapiocaClient with the data wrapped inside.
        :rtype: TapiocaClient
        """
        request_kwargs = kwargs.pop("request_kwargs", self._request_kwargs)
        return TapiocaClient(
            self._instatiate_api(),
            data=data,
            api_params=self._api_params,
            request_kwargs=request_kwargs,
            refresh_token_by_default=self._refresh_token_default,
            refresh_data=self._refresh_data,
            session=self._session,
            *args,
            **kwargs,
        )

    def _wrap_in_tapioca_executor(self, data, *args, **kwargs):
        """
        Wrap the data in a TapiocaClientExecutor.

        :param data: Any data to be wrapped.
        :type data: Any
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :returns: Instance of TapiocaClientExecutor with the data wrapped inside.
        :rtype: TapiocaClientExecutor
        """
        request_kwargs = kwargs.pop("request_kwargs", self._request_kwargs)
        return TapiocaClientExecutor(
            self._instatiate_api(),
            data=data,
            api_params=self._api_params,
            request_kwargs=request_kwargs,
            refresh_token_by_default=self._refresh_token_default,
            refresh_data=self._refresh_data,
            session=self._session,
            *args,
            **kwargs,
        )

    def _get_doc(self):
        """
        Get the documentation string for this class.

        :returns: The documentation string.
        :rtype: str
        """
        resources = copy.copy(self._resource)
        docs = (
            "Automatic generated __doc__ from resource_mapping.\n"
            "Resource: %s\n"
            "Docs: %s\n" % (resources.pop("resource", ""), resources.pop("docs", ""))
        )
        for key, value in sorted(resources.items()):
            docs += "%s: %s\n" % (key.title(), value)
        docs = docs.strip()
        return docs

    __doc__ = property(_get_doc)

    def __call__(self, *args, **kwargs):
        """
        Call function for the class.

        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :returns: An instance of TapiocaClientExecutor.
        :rtype: TapiocaClientExecutor
        """
        data = self._data

        url_params = self._api_params.get("default_url_params", {})
        url_params.update(kwargs)
        if self._resource and url_params:
            data = self._api.fill_resource_template_url(self._data, url_params)

        return self._wrap_in_tapioca_executor(
            data, resource=self._resource, response=self._response
        )

    def _to_camel_case(self, name):
        """
        Convert a snake_case string in CamelCase.

        :param name: String in snake_case.
        :type name: str
        :returns: The string converted to CamelCase.
        :rtype: str
        """
        if isinstance(name, int):
            return name
        components = name.split("_")
        return components[0] + "".join(x.title() for x in components[1:])

    def _get_client_from_name(self, name):
        """
        Get a client with the specified name.

        :param name: Name of the client.
        :type name: str
        :returns: Client if it exists, None otherwise.
        :rtype: TapiocaClient or None
        """
        if (
            isinstance(self._data, list)
            and isinstance(name, int)
            or callable(getattr(self._data, "__iter__", None))
            and name in self._data
        ):
            return self._wrap_in_tapioca(data=self._data[name])

        # if you could not access, fallback to resource mapping
        resource_mapping = self._api.resource_mapping
        if name in resource_mapping:
            resource = resource_mapping[name]
            api_root = self._api.get_api_root(self._api_params, resource_name=name)

            url = api_root.rstrip("/") + "/" + resource["resource"].lstrip("/")
            return self._wrap_in_tapioca(url, resource=resource)  # Pass the resource parameter here

        return None

    def _get_client_from_name_or_fallback(self, name):
        """
        Try to get a client with the specified name, try some variations if not found.

        :param name: Name of the client.
        :type name: str
        :returns: Client if it exists, None otherwise.
        :rtype: TapiocaClient or None
        """
        client = self._get_client_from_name(name)
        if client is not None:
            return client

        camel_case_name = self._to_camel_case(name)
        client = self._get_client_from_name(camel_case_name)
        if client is not None:
            return client

        normal_camel_case_name = camel_case_name[0].upper()
        normal_camel_case_name += camel_case_name[1:]

        client = self._get_client_from_name(normal_camel_case_name)
        return client if client is not None else None

    def __getattr__(self, name):
        if name in ['_data', '__setstate__']:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        ret = self._get_client_from_name_or_fallback(name)
        if ret is None:
            raise AttributeError(name)
        return ret

    def __getitem__(self, key):
        ret = self._get_client_from_name_or_fallback(key)
        if ret is None:
            raise KeyError(key)
        return ret

    def __dir__(self):
        if self._api and self._data is None:
            return list(self._api.resource_mapping.keys())

        return self._data.keys() if isinstance(self._data, dict) else []

    def __str__(self):
        if type(self._data) == OrderedDict:
            return "<{} object, printing as dict:\n" "{}>".format(
                self.__class__.__name__, json.dumps(self._data, indent=4)
            )
        import pprint

        pp = pprint.PrettyPrinter(indent=4)
        return f"<{self.__class__.__name__} object\n{pp.pformat(self._data)}>"

    def _repr_pretty_(self, p, cycle):
        p.text(self.__str__())

    def __len__(self):
        return len(self._data)

    def __contains__(self, key):
        return key in self._data


class TapiocaClientExecutor(TapiocaClient):
    """
    Subclass of `TapiocaClient` with additional methods for executing requests and handling responses.
    """
    def __init__(self, api, *args, **kwargs):
        """
        Initialize a TapiocaClientExecutor instance.

        :param api: An API object.
        :type api: Any
        """
        super().__init__(api, *args, **kwargs)

    def __getitem__(self, key):
        """
        Prevent item retrieval.

        :param key: Key value.
        :type key: str
        :raises Exception: Always raised to prevent this operation.
        """
        raise Exception("This operation cannot be done on a TapiocaClientExecutor object")

    def __iter__(self):
        """
        Prevent iteration.

        :raises Exception: Always raised to prevent this operation.
        """
        raise Exception("Cannot iterate over a TapiocaClientExecutor object")

    def __getattr__(self, name):
        """
        Handle attribute retrieval.

        :param name: Attribute name.
        :type name: str
        :returns: Method or wrapped executor, depending on the attribute.
        :rtype: Any
        """
        if name.startswith("to_"):
            return self._api._get_to_native_method(name, self._data)
        return self._wrap_in_tapioca_executor(getattr(self._data, name))

    def __call__(self, *args, **kwargs):
        """
        Call this instance.

        :returns: Wrapped executor.
        :rtype: Any
        """
        return self._wrap_in_tapioca(self._data.__call__(*args, **kwargs))

    @property
    def data(self):
        """
        Get the data.

        :returns: The data.
        :rtype: Any
        """
        return self._data

    @property
    def response(self):
        """
        Get the response.

        :raises Exception: If there's no response object associated with this instance.
        :returns: The response if it exists.
        :rtype: Any
        """
        if self._response is None:
            raise Exception("This instance has no response object")
        return self._response

    @property
    def status_code(self):
        """
        Get the status code from the response.

        :returns: The status code.
        :rtype: int
        """
        return self.response.status_code

    @property
    def refresh_data(self):
        """
        Get the refreshed data.

        :returns: The refreshed data.
        :rtype: Any
        """
        return self._refresh_data

    def _make_request(self, request_method, refresh_token=None, *args, **kwargs):
        """
        Make a request to the API.

        :param request_method: The type of the request ("GET", "POST", etc.)
        :type request_method: str
        :param refresh_token: Flag indicating whether the token should be refreshed.
        :type refresh_token: bool, optional
        :returns: Response from the API call.
        :rtype: Any
        """
        if "url" not in kwargs:
            kwargs["url"] = self._data

        request_kwargs = self._api.get_request_kwargs(
            self._api_params, request_method, *args, **kwargs
        )

        response = self._session.request(request_method, **request_kwargs)

        # Extract rate limit headers
        remaining_requests = int(response.headers.get("X-RateLimit-Remaining", 1))
        reset_time = int(response.headers.get("X-RateLimit-Reset", 0))

        # Set a threshold for remaining requests
        threshold = 100

        # Calculate delay based on remaining requests and reset time
        if remaining_requests <= threshold and reset_time > 0:
            delay = reset_time / remaining_requests
            time.sleep(delay)

        try:
            data = self._api.process_response(response)
        except ResponseProcessException as e:
            client = self._wrap_in_tapioca(
                e.data, response=response, request_kwargs=request_kwargs
            )

            error_message = self._api.get_error_message(data=e.data, response=response)
            tapioca_exception = e.tapioca_exception(message=error_message, client=client)

            should_refresh_token = refresh_token is not False and self._refresh_token_default
            auth_expired = self._api.is_authentication_expired(tapioca_exception)

            propagate_exception = True

            if should_refresh_token and auth_expired:
                self._refresh_data = self._api.refresh_authentication(self._api_params)
                if self._refresh_data:
                    propagate_exception = False
                    return self._make_request(request_method, refresh_token=False, *args, **kwargs)

            if propagate_exception:
                raise tapioca_exception from e

        return self._wrap_in_tapioca(data, response=response, request_kwargs=request_kwargs)

    def get(self, *args, **kwargs):
        """
        Make a GET request.

        :returns: Response from the API call.
        :rtype: Any
        """
        return self._make_request("GET", *args, **kwargs)

    def post(self, *args, **kwargs):
        return self._make_request("POST", *args, **kwargs)

    def options(self, *args, **kwargs):
        return self._make_request("OPTIONS", *args, **kwargs)

    def put(self, *args, **kwargs):
        return self._make_request("PUT", *args, **kwargs)

    def patch(self, *args, **kwargs):
        return self._make_request("PATCH", *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self._make_request("DELETE", *args, **kwargs)

    def _get_iterator_list(self):
        """
        Get the iterator list.

        :returns: Iterator list.
        :rtype: Any
        """
        return self._api.get_iterator_list(self._data)

    def _get_iterator_next_request_kwargs(self):
        """
        Get the next request kwargs for the iterator.

        :returns: Next request kwargs.
        :rtype: Any
        """
        print("do we ever hit this point")
        return self._api.get_iterator_next_request_kwargs(
            self._request_kwargs, self._data, self._response
        )

    def _reached_max_limits(self, page_count, item_count, max_pages, max_items):
        """
        Check if the maximum limits have been reached.

        :param page_count: Current page count.
        :type page_count: int
        :param item_count: Current item count.
        :type item_count: int
        :param max_pages: Maximum number of pages.
        :type max_pages: int, optional
        :param max_items: Maximum number of items.
        :type max_items: int, optional
        :returns: Whether the maximum limits have been reached.
        :rtype: bool
        """
        reached_page_limit = max_pages is not None and max_pages <= page_count
        reached_item_limit = max_items is not None and max_items <= item_count
        return reached_page_limit or reached_item_limit

    def pages(self, max_pages=None, max_items=None, **kwargs):
        """
        Get the pages.

        :param max_pages: Maximum number of pages.
        :type max_pages: int, optional
        :param max_items: Maximum number of items.
        :type max_items: int, optional
        :returns: Pages.
        :rtype: Any
        """
        executor = self
        print("heres the first time")
        iterator_list = executor._get_iterator_list()
        print("iterator list", iterator_list)

        page_count = 0
        item_count = 0

        while iterator_list and not self._reached_max_limits(page_count, item_count, max_pages, max_items):
            for item in iterator_list:
                if self._reached_max_limits(page_count, item_count, max_pages, max_items):
                    break
                yield self._wrap_in_tapioca(item)
                item_count += 1

            page_count += 1

            print("About to call get_iterator_next_request_kwargs")
            next_request_kwargs = executor._get_iterator_next_request_kwargs()
            print("Finished calling get_iterator_next_request_kwargs")

            if not next_request_kwargs:
                break

            response = self.get(**next_request_kwargs)
            executor = response()
            iterator_list = executor._get_iterator_list()

    def open_docs(self):
        if not self._resource:
            raise KeyError()

        new = 2  # open in new tab
        webbrowser.open(self._resource["docs"], new=new)

    def open_in_browser(self):
        """
        Open the data in a new browser tab.
        """
        new = 2  # open in new tab
        webbrowser.open(self._data, new=new)

    def __dir__(self):
        """
        Get a list of methods that don't start with an underscore ("_").

        :returns: List of method names.
        :rtype: List[str]
        """
        methods = [m for m in TapiocaClientExecutor.__dict__.keys() if not m.startswith("_")]
        methods += [m for m in dir(self._api.serializer) if m.startswith("to_")]

        return methods
