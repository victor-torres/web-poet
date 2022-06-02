"""Contains some internal definitions that is internal to **web-poet**.

In general, users shouldn't import and use the contents of this module.
"""

from urllib.parse import urljoin
from typing import Type, TypeVar, List, Dict, Union

from multidict import CIMultiDict
from w3lib.url import add_or_replace_parameters

T_headers = TypeVar("T_headers", bound="_HttpHeaders")
T_url = TypeVar("T_url", bound="_Url")


class _HttpHeaders(CIMultiDict):
    """A base container for holding the HTTP headers.

    For more info on its other features, read the API spec of
    :class:`multidict.CIMultiDict`.
    """

    @classmethod
    def from_name_value_pairs(cls: Type[T_headers], arg: List[Dict]) -> T_headers:
        """An alternative constructor for instantiation using a ``List[Dict]``
        where the 'key' is the header name while the 'value' is the header value.

        >>> pairs = [
        ...     {"name": "Content-Encoding", "value": "gzip"},
        ...     {"name": "content-length", "value": "648"}
        ... ]
        >>> headers = _HttpHeaders.from_name_value_pairs(pairs)
        >>> headers
        <_HttpHeaders('Content-Encoding': 'gzip', 'content-length': '648')>
        """
        return cls([(pair["name"], pair["value"]) for pair in arg])


class _Url:
    """ Base URL class.
    """
    def __init__(self, url: Union[str, '_Url']):
        if not isinstance(url, (str, _Url)):
            raise TypeError(f"`url` must be a str or an instance of _Url, "
                            f"got {url.__class__} instance instead")
        self._url = str(url)

    def join(self: T_url, other: Union[str, '_Url']) -> T_url:
        return self.__class__(urljoin(self._url, str(other)))

    def update_query(self: T_url,
                     new_parameters: Dict[str, str]) -> T_url:
        new_url = add_or_replace_parameters(self._url,
                                            new_parameters=new_parameters)
        return self.__class__(new_url)

    def __str__(self) -> str:
        return self._url

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._url!r})"

    def __mod__(self: T_url, other: Dict[str, str]) -> T_url:
        return self.update_query(other)

    __truediv__ = join
