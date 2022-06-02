import pytest

from web_poet._base import _Url


def test_url_base_class():
    url_str = "http://example.com"
    url = _Url(url_str)
    assert str(url) == url_str
    assert repr(url) == "_Url('http://example.com')"


def test_url_init_validation():
    with pytest.raises(TypeError):
        _Url(123)


def test_url_subclasses():
    url_str = "http://example.com"

    class MyUrl(_Url):
        pass

    class MyUrl2(_Url):
        pass

    url = MyUrl(url_str)
    assert str(url) == url_str
    assert url._url == url_str
    assert repr(url) == "MyUrl('http://example.com')"

    url2 = MyUrl2(url)
    assert str(url2) == str(url)


def test_urljoin():
    url = _Url("http://example.com/foo/bar?x=y#fragment")
    assert str(url.join("baz")) == "http://example.com/foo/baz"
    assert str(url / "baz") == "http://example.com/foo/baz"


def test_update_query():
    url = _Url("http://example.com/foo/bar?x=y#fragment")
    assert str(url % {"foo": "bar"}) == "http://example.com/foo/bar?x=y&foo=bar#fragment"
    assert str(url % {"x": "z"}) == "http://example.com/foo/bar?x=z#fragment"