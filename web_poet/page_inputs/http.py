import json
from typing import Optional, Dict, List, Type, TypeVar, Union, Tuple, AnyStr

import attrs
from w3lib.encoding import (
    html_to_unicode,
    html_body_declared_encoding,
    resolve_encoding,
    http_content_type_encoding
)

import yarl
from web_poet._base import _HttpHeaders
from web_poet.utils import memoizemethod_noargs
from web_poet.mixins import SelectableMixin

T_headers = TypeVar("T_headers", bound="HttpResponseHeaders")

_AnyStrDict = Dict[AnyStr, Union[AnyStr, List[AnyStr], Tuple[AnyStr, ...]]]


class _Url:
    def __init__(self, url: Union[str, yarl.URL], encoded=True):
        self._url = yarl.URL(str(url), encoded=encoded)

    def __str__(self) -> str:
        return str(self._url)

    def __repr__(self) -> str:
        return f'{type(self).__name__}({str(self._url)!r})'

    def __eq__(self, other) -> bool:
        if self._url.path == "/":
            if isinstance(other, str):
                other = _Url(other)
            if self._url.path == other.path:
                return True
        return str(self._url) == str(other)

    @property
    def scheme(self) -> str:
        return self._url.scheme

    @property
    def host(self) -> Optional[str]:
        return self._url.host

    @property
    def path(self) -> str:
        return self._url.path

    @property
    def query_string(self) -> str:
        return self._url.query_string

    @property
    def fragment(self) -> str:
        return self._url.fragment


class ResponseUrl(_Url):
    """ URL of the response

    :param url: a string representation of a URL.
    :param encoded: If set to False, the given ``url`` would be auto-encoded.
        However, there's no guarantee that correct encoding is used. Thus,
        it's recommended to set this in the *default* ``False`` value.
    """
    pass


class RequestUrl(_Url):
    """ URL of the request

    :param url: a string representation of a URL.
    :param encoded: If set to False, the given ``url`` would be auto-encoded.
        However, there's no guarantee that correct encoding is used. Thus,
        it's recommended to set this in the *default* ``False`` value.
    """
    pass


class HttpRequestBody(bytes):
    """A container for holding the raw HTTP request body in bytes format."""

    pass


class HttpResponseBody(bytes):
    """A container for holding the raw HTTP response body in bytes format."""

    def declared_encoding(self) -> Optional[str]:
        """ Return the encoding specified in meta tags in the html body,
        or ``None`` if no suitable encoding was found """
        return html_body_declared_encoding(self)

    def json(self):
        """
        Deserialize a JSON document to a Python object.
        """
        return json.loads(self)


class HttpRequestHeaders(_HttpHeaders):
    """A container for holding the HTTP request headers.

    It's able to accept instantiation via an Iterable of Tuples:

    >>> pairs = [("Content-Encoding", "gzip"), ("content-length", "648")]
    >>> HttpRequestHeaders(pairs)
    <HttpRequestHeaders('Content-Encoding': 'gzip', 'content-length': '648')>

    It's also accepts a mapping of key-value pairs as well:

    >>> pairs = {"Content-Encoding": "gzip", "content-length": "648"}
    >>> headers = HttpRequestHeaders(pairs)
    >>> headers
    <HttpRequestHeaders('Content-Encoding': 'gzip', 'content-length': '648')>

    Note that this also supports case insensitive header-key lookups:

    >>> headers.get("content-encoding")
    'gzip'
    >>> headers.get("Content-Length")
    '648'

    These are just a few of the functionalities it inherits from
    :class:`multidict.CIMultiDict`. For more info on its other features, read
    the API spec of :class:`multidict.CIMultiDict`.
    """

    pass


class HttpResponseHeaders(_HttpHeaders):
    """A container for holding the HTTP response headers.

    It's able to accept instantiation via an Iterable of Tuples:

    >>> pairs = [("Content-Encoding", "gzip"), ("content-length", "648")]
    >>> HttpResponseHeaders(pairs)
    <HttpResponseHeaders('Content-Encoding': 'gzip', 'content-length': '648')>

    It's also accepts a mapping of key-value pairs as well:

    >>> pairs = {"Content-Encoding": "gzip", "content-length": "648"}
    >>> headers = HttpResponseHeaders(pairs)
    >>> headers
    <HttpResponseHeaders('Content-Encoding': 'gzip', 'content-length': '648')>

    Note that this also supports case insensitive header-key lookups:

    >>> headers.get("content-encoding")
    'gzip'
    >>> headers.get("Content-Length")
    '648'

    These are just a few of the functionalities it inherits from
    :class:`multidict.CIMultiDict`. For more info on its other features, read
    the API spec of :class:`multidict.CIMultiDict`.
    """

    @classmethod
    def from_bytes_dict(
        cls: Type[T_headers], arg: _AnyStrDict, encoding: str = "utf-8"
    ) -> T_headers:
        """An alternative constructor for instantiation where the header-value
        pairs could be in raw bytes form.

        This supports multiple header values in the form of ``List[bytes]`` and
        ``Tuple[bytes]]`` alongside a plain ``bytes`` value. A value in ``str``
        also works and wouldn't break the decoding process at all.

        By default, it converts the ``bytes`` value using "utf-8". However, this
        can easily be overridden using the ``encoding`` parameter.

        >>> raw_values = {
        ...     b"Content-Encoding": [b"gzip", b"br"],
        ...     b"Content-Type": [b"text/html"],
        ...     b"content-length": b"648",
        ... }
        >>> headers = HttpResponseHeaders.from_bytes_dict(raw_values)
        >>> headers
        <HttpResponseHeaders('Content-Encoding': 'gzip', 'Content-Encoding': 'br', 'Content-Type': 'text/html', 'content-length': '648')>
        """

        def _norm(data):
            if isinstance(data, str) or data is None:
                return data
            elif isinstance(data, bytes):
                return data.decode(encoding)
            raise ValueError(f"Expecting str or bytes. Received {type(data)}")

        converted = []

        for header, value in arg.items():
            if isinstance(value, list) or isinstance(value, tuple):
                converted.extend([(_norm(header), _norm(v)) for v in value])
            else:
                converted.append((_norm(header), _norm(value)))

        return cls(converted)

    def declared_encoding(self) -> Optional[str]:
        """ Return encoding detected from the Content-Type header, or None
        if encoding is not found """
        content_type = self.get('Content-Type', '')
        return http_content_type_encoding(content_type)


@attrs.define(auto_attribs=False, slots=False, eq=False)
class HttpRequest:
    """Represents a generic HTTP request used by other functionalities in
    **web-poet** like :class:`~.HttpClient`.
    """

    url: RequestUrl = attrs.field(converter=RequestUrl)
    method: str = attrs.field(default="GET", kw_only=True)
    headers: HttpRequestHeaders = attrs.field(
        factory=HttpRequestHeaders, converter=HttpRequestHeaders, kw_only=True
    )
    body: HttpRequestBody = attrs.field(
        factory=HttpRequestBody, converter=HttpRequestBody, kw_only=True
    )


@attrs.define(auto_attribs=False, slots=False, eq=False)
class HttpResponse(SelectableMixin):
    """A container for the contents of a response, downloaded directly using an
    HTTP client.

    ``url`` should be a URL of the response (after all redirects),
    not a URL of the request, if possible.

    ``body`` contains the raw HTTP response body.

    The following are optional since it would depend on the source of the
    ``HttpResponse`` if these are available or not. For example, the responses
    could simply come off from a local HTML file which doesn't contain ``headers``
    and ``status``.

    ``status`` should represent the int status code of the HTTP response.

    ``headers`` should contain the HTTP response headers.

    ``encoding`` encoding of the response. If None (default), encoding
    is auto-detected from headers and body content.
    """

    url: ResponseUrl = attrs.field(converter=ResponseUrl)
    body: HttpResponseBody = attrs.field(converter=HttpResponseBody)
    status: Optional[int] = attrs.field(default=None, kw_only=True)
    headers: HttpResponseHeaders = attrs.field(factory=HttpResponseHeaders,
                                               converter=HttpResponseHeaders,
                                               kw_only=True)
    _encoding: Optional[str] = attrs.field(default=None, kw_only=True)

    _DEFAULT_ENCODING = 'ascii'
    _cached_text: Optional[str] = None

    @property
    def text(self) -> str:
        """
        Content of the HTTP body, converted to unicode
        using the detected encoding of the response, according
        to the web browser rules (respecting Content-Type header, etc.)
        """
        # Access self.encoding before self._cached_text, because
        # there is a chance self._cached_text would be already populated
        # while detecting the encoding
        encoding = self.encoding
        if self._cached_text is None:
            fake_content_type_header = f'charset={encoding}'
            encoding, text = html_to_unicode(fake_content_type_header, self.body)
            self._cached_text = text
        return self._cached_text

    def _selector_input(self) -> str:
        return self.text

    @property
    def encoding(self):
        """ Encoding of the response """
        return (
            self._encoding
            or self._headers_declared_encoding()
            or self._body_declared_encoding()
            or self._body_inferred_encoding()
        )

    @memoizemethod_noargs
    def json(self):
        """ Deserialize a JSON document to a Python object. """
        return self.body.json()

    @memoizemethod_noargs
    def _headers_declared_encoding(self):
        return self.headers.declared_encoding()

    @memoizemethod_noargs
    def _body_declared_encoding(self):
        return self.body.declared_encoding()

    @memoizemethod_noargs
    def _body_inferred_encoding(self):
        content_type = self.headers.get('Content-Type', '')
        body_encoding, text = html_to_unicode(
            content_type,
            self.body,
            auto_detect_fun=self._auto_detect_fun,
            default_encoding=self._DEFAULT_ENCODING
        )
        self._cached_text = text
        return body_encoding

    def _auto_detect_fun(self, body: bytes) -> Optional[str]:
        for enc in (self._DEFAULT_ENCODING, 'utf-8', 'cp1252'):
            try:
                body.decode(enc)
            except UnicodeError:
                continue
            return resolve_encoding(enc)
