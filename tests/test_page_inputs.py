import json

import aiohttp.web_response
import pytest
import requests

import parsel
from web_poet.page_inputs import (
    RequestUrl,
    ResponseUrl,
    HttpRequest,
    HttpResponse,
    HttpRequestBody,
    HttpResponseBody,
    HttpRequestHeaders,
    HttpResponseHeaders,
    BrowserHtml,
)


@pytest.mark.parametrize("cls", [RequestUrl, ResponseUrl])
def test_url(cls):
    url_value = "https://example.com/category/product?query=123&id=xyz#frag1"

    url = cls(url_value)

    assert str(url) == url_value
    assert url.scheme == "https"
    assert url.host == "example.com"
    assert url.path == "/category/product"
    assert url.query_string == "query=123&id=xyz"
    assert url.fragment == "frag1"

    new_url = cls(url)
    assert url == new_url
    assert str(url) == str(new_url)


@pytest.mark.parametrize("compare_cls", [True, False])
@pytest.mark.parametrize("cls", [RequestUrl, ResponseUrl])
def test_url_equality(compare_cls, cls):
    # Trailing / in the base URL
    no_trail = cls("https://example.com")
    with_trail = "https://example.com/"
    if compare_cls:
        with_trail = cls(with_trail)
    assert no_trail == with_trail
    assert str(no_trail) != str(with_trail)

    # Trailing / in the path URL
    no_trail = cls("https://example.com/foo")
    with_trail = "https://example.com/foo/"
    if compare_cls:
        with_trail = cls(with_trail)
    assert no_trail != with_trail  # Should not be equal
    assert str(no_trail) != str(with_trail)


@pytest.mark.parametrize("cls", [RequestUrl, ResponseUrl])
def test_url_encoding(cls):
    url_value = "http://εμπορικόσήμα.eu/путь/這裡"

    url = cls(url_value)
    str(url) == url_value

    url = cls(url_value, encoded=False)
    str(url) == "http://xn--jxagkqfkduily1i.eu/%D0%BF%D1%83%D1%82%D1%8C/%E9%80%99%E8%A3%A1"


@pytest.mark.parametrize("body_cls", [HttpRequestBody, HttpResponseBody])
def test_http_body_hashable(body_cls):
    http_body = body_cls(b"content")
    assert http_body in {http_body}
    assert http_body in {b"content"}
    assert http_body not in {b"foo"}


@pytest.mark.parametrize("body_cls", [HttpRequestBody, HttpResponseBody])
def test_http_body_bytes_api(body_cls):
    http_body = body_cls(b"content")
    assert http_body == b"content"
    assert b"ent" in http_body


@pytest.mark.parametrize("body_cls", [HttpRequestBody, HttpResponseBody])
def test_http_body_str_api(body_cls):
    with pytest.raises(TypeError):
        body_cls("string content")


def test_http_response_body_declared_encoding():
    http_body = HttpResponseBody(b"content")
    assert http_body.declared_encoding() is None

    http_body = HttpResponseBody(b"""
    <html><head>
    <meta charset="utf-8" />
    </head></html>
    """)
    assert http_body.declared_encoding() == "utf-8"


def test_http_response_body_json():
    http_body = HttpResponseBody(b"content")
    with pytest.raises(json.JSONDecodeError):
        data = http_body.json()

    http_body = HttpResponseBody(b'{"foo": 123}')
    assert http_body.json() == {"foo": 123}

    http_body = HttpResponseBody('{"ключ": "значение"}'.encode("utf8"))
    assert http_body.json() == {"ключ": "значение"}


@pytest.mark.parametrize(
    ["cls", "body_cls"],
    [
        (HttpRequest, HttpRequestBody),
        (HttpResponse, HttpResponseBody),
    ]
)
def test_http_defaults(cls, body_cls):
    http_body = body_cls(b"content")

    obj = cls("url", body=http_body)
    assert obj.url == "url"
    assert obj.body == b"content"
    assert not obj.headers
    assert obj.headers.get("user-agent") is None

    if cls == HttpResponse:
        assert obj.status is None
    else:
        with pytest.raises(AttributeError):
            obj.status


@pytest.mark.parametrize(
    ["cls", "headers_cls"],
    [
        (HttpRequest, HttpRequestHeaders),
        (HttpResponse, HttpResponseHeaders),
    ]
)
def test_http_with_headers_alt_constructor(cls, headers_cls):
    headers = headers_cls.from_name_value_pairs([{"name": "User-Agent", "value": "test agent"}])
    obj = cls("url", body=b"", headers=headers)
    assert len(obj.headers) == 1
    assert obj.headers.get("user-agent") == "test agent"


@pytest.mark.parametrize(
    ["cls", "body_cls"],
    [
        (HttpRequest, HttpRequestBody),
        (HttpResponse, HttpResponseBody),
    ]
)
def test_http_response_bytes_body(cls, body_cls):
    obj = cls("http://example.com", body=b"content")
    assert isinstance(obj.body, body_cls)
    assert obj.body == body_cls(b"content")


@pytest.mark.parametrize("cls", [HttpRequest, HttpResponse])
def test_http_body_validation_str(cls):
    with pytest.raises(TypeError):
        cls("http://example.com", body="content")


@pytest.mark.parametrize("cls", [HttpRequest, HttpResponse])
def test_http_body_validation_None(cls):
    with pytest.raises(TypeError):
        cls("http://example.com", body=None)


@pytest.mark.xfail(reason="not implemented")
@pytest.mark.parametrize("cls", [HttpRequest, HttpResponse])
def test_http_body_validation_other(cls):
    with pytest.raises(TypeError):
        cls("http://example.com", body=123)


@pytest.mark.parametrize("cls", [HttpRequest, HttpResponse])
def test_http_request_headers_init_invalid(cls):
    with pytest.raises(TypeError):
        cls("http://example.com", body=b"", headers=123)


@pytest.mark.parametrize("headers_cls", [HttpRequestHeaders, HttpResponseHeaders])
def test_http_response_headers(headers_cls):
    headers = headers_cls({"user-agent": "mozilla"})
    assert headers['user-agent'] == "mozilla"
    assert headers['User-Agent'] == "mozilla"

    with pytest.raises(KeyError):
        headers["user agent"]


@pytest.mark.parametrize(
    ["cls", "headers_cls"],
    [
        (HttpRequest, HttpRequestHeaders),
        (HttpResponse, HttpResponseHeaders),
    ]
)
def test_http_headers_init_dict(cls, headers_cls):
    obj = cls(
        "http://example.com", body=b"", headers={"user-agent": "chrome"}
    )
    assert isinstance(obj.headers, headers_cls)
    assert obj.headers['user-agent'] == "chrome"
    assert obj.headers['User-Agent'] == "chrome"


def test_http_request_init_minimal():
    req = HttpRequest("url")
    assert req.url == "url"
    assert req.method == "GET"
    assert isinstance(req.method, str)
    assert not req.headers
    assert isinstance(req.headers, HttpRequestHeaders)
    assert not req.body
    assert isinstance(req.body, HttpRequestBody)


def test_http_request_init_full():
    req_1 = HttpRequest(
        "url", method="POST", headers={"User-Agent": "test agent"}, body=b"body"
    )
    assert req_1.method == "POST"
    assert isinstance(req_1.method, str)
    assert req_1.headers == {"User-Agent": "test agent"}
    assert req_1.headers.get("user-agent") == "test agent"
    assert isinstance(req_1.headers, HttpRequestHeaders)
    assert req_1.body == b"body"
    assert isinstance(req_1.body, HttpRequestBody)

    http_headers = HttpRequestHeaders({"User-Agent": "test agent"})
    http_body = HttpRequestBody(b"body")
    req_2 = HttpRequest("url", method="POST", headers=http_headers, body=http_body)

    assert req_1.url == req_2.url
    assert req_1.method == req_2.method
    assert req_1.headers == req_2.headers
    assert req_1.body == req_2.body


def test_http_response_headers_from_bytes_dict():
    raw_headers = {
        b"Content-Length": [b"316"],
        b"Content-Encoding": [b"gzip", b"br"],
        b"server": b"sffe",
        "X-string": "string",
        "X-missing": None,
        "X-tuple": (b"x", "y"),
    }
    headers = HttpResponseHeaders.from_bytes_dict(raw_headers)

    assert headers.get("content-length") == "316"
    assert headers.get("content-encoding") == "gzip"
    assert headers.getall("Content-Encoding") == ["gzip", "br"]
    assert headers.get("server") == "sffe"
    assert headers.get("x-string") == "string"
    assert headers.get("x-missing") is None
    assert headers.get("x-tuple") == "x"
    assert headers.getall("x-tuple") == ["x", "y"]


def test_http_response_headers_from_bytes_dict_err():

    with pytest.raises(ValueError):
        HttpResponseHeaders.from_bytes_dict({b"Content-Length": [316]})

    with pytest.raises(ValueError):
        HttpResponseHeaders.from_bytes_dict({b"Content-Length": 316})


def test_http_response_headers_init_requests():
    requests_response = requests.Response()
    requests_response.headers['User-Agent'] = "mozilla"

    response = HttpResponse("http://example.com", body=b"",
                            headers=requests_response.headers)
    assert isinstance(response.headers, HttpResponseHeaders)
    assert response.headers['user-agent'] == "mozilla"
    assert response.headers['User-Agent'] == "mozilla"


def test_http_response_headers_init_aiohttp():
    aiohttp_response = aiohttp.web_response.Response()
    aiohttp_response.headers['User-Agent'] = "mozilla"

    response = HttpResponse("http://example.com", body=b"",
                            headers=aiohttp_response.headers)
    assert isinstance(response.headers, HttpResponseHeaders)
    assert response.headers['user-agent'] == "mozilla"
    assert response.headers['User-Agent'] == "mozilla"


def test_http_response_selectors(book_list_html_response):
    title = "All products | Books to Scrape - Sandbox"

    assert title == book_list_html_response.css("title ::text").get("").strip()
    assert title == book_list_html_response.xpath("//title/text()").get("").strip()


def test_http_response_json():
    url = "http://example.com"

    with pytest.raises(json.JSONDecodeError):
        response = HttpResponse(url, body=b'non json')
        response.json()

    response = HttpResponse(url, body=b'{"key": "value"}')
    assert response.json() == {"key": "value"}

    response = HttpResponse(url, body='{"ключ": "значение"}'.encode("utf8"))
    assert response.json() == {"ключ": "значение"}


def test_http_response_text():
    """This tests a character which raises a UnicodeDecodeError when decoded in
    'ascii'.

    The backup series of encodings for decoding should be able to handle it.
    """
    text = "œ is a Weird Character"
    body = HttpResponseBody(b"\x9c is a Weird Character")
    response = HttpResponse("http://example.com", body=body)

    assert response.text == text


@pytest.mark.parametrize(["headers", "encoding"], [
    ({"Content-type": "text/html; charset=utf-8"}, "utf-8"),
    ({"Content-type": "text/html; charset=UTF8"}, "utf-8"),
    ({}, None),
    ({"Content-type": "text/html; charset=iso-8859-1"}, "cp1252"),
    ({"Content-type": "text/html; charset=None"}, None),
    ({"Content-type": "text/html; charset=gb2312"}, "gb18030"),
    ({"Content-type": "text/html; charset=gbk"}, "gb18030"),
    ({"Content-type": "text/html; charset=UNKNOWN"}, None),
])
def test_http_headers_declared_encoding(headers, encoding):
    headers = HttpResponseHeaders(headers)
    assert headers.declared_encoding() == encoding

    response = HttpResponse("http://example.com", body=b'', headers=headers)
    assert response.encoding == encoding or HttpResponse._DEFAULT_ENCODING


def test_http_response_utf16():
    """Test utf-16 because UnicodeDammit is known to have problems with"""
    r = HttpResponse("http://www.example.com",
                     body=b'\xff\xfeh\x00i\x00',
                     encoding='utf-16')
    assert r.text == "hi"
    assert r.encoding == "utf-16"


def test_explicit_encoding():
    response = HttpResponse("http://www.example.com", "£".encode('utf-8'),
                            encoding='utf-8')
    assert response.encoding == "utf-8"
    assert response.text == "£"


def test_explicit_encoding_invalid():
    response = HttpResponse("http://www.example.com", body="£".encode('utf-8'),
                            encoding='latin1')
    assert response.encoding == "latin1"
    assert response.text == "£".encode('utf-8').decode("latin1")


def test_utf8_body_detection():
    response = HttpResponse("http://www.example.com", b"\xc2\xa3",
                            headers={"Content-type": "text/html; charset=None"})
    assert response.encoding == "utf-8"

    response = HttpResponse("http://www.example.com", body=b"\xc2",
                            headers={"Content-type": "text/html; charset=None"})
    assert response.encoding != "utf-8"


def test_gb2312():
    response = HttpResponse("http://www.example.com", body=b"\xa8D",
                            headers={"Content-type": "text/html; charset=gb2312"})
    assert response.text == "\u2015"


def test_invalid_utf8_encoded_body_with_valid_utf8_BOM():
    response = HttpResponse("http://www.example.com",
                            headers={"Content-type": "text/html; charset=utf-8"},
                            body=b"\xef\xbb\xbfWORD\xe3\xab")
    assert response.encoding == "utf-8"
    assert response.text == 'WORD\ufffd'


def test_bom_is_removed_from_body():
    # Inferring encoding from body also cache decoded body as sideeffect,
    # this test tries to ensure that calling response.encoding and
    # response.text in indistint order doesn't affect final
    # values for encoding and decoded body.
    url = 'http://example.com'
    body = b"\xef\xbb\xbfWORD"
    headers = {"Content-type": "text/html; charset=utf-8"}

    # Test response without content-type and BOM encoding
    response = HttpResponse(url, body=body)
    assert response.encoding == "utf-8"
    assert response.text == "WORD"
    response = HttpResponse(url, body=body)
    assert response.text == "WORD"
    assert response.encoding == "utf-8"

    # Body caching sideeffect isn't triggered when encoding is declared in
    # content-type header but BOM still need to be removed from decoded
    # body
    response = HttpResponse(url, headers=headers, body=body)
    assert response.encoding == "utf-8"
    assert response.text == "WORD"
    response = HttpResponse(url, headers=headers, body=body)
    assert response.text == "WORD"
    assert response.encoding == "utf-8"


def test_replace_wrong_encoding():
    """Test invalid chars are replaced properly"""
    r = HttpResponse("http://www.example.com", encoding='utf-8',
                     body=b'PREFIX\xe3\xabSUFFIX')
    # XXX: Policy for replacing invalid chars may suffer minor variations
    # but it should always contain the unicode replacement char ('\ufffd')
    assert '\ufffd' in r.text, repr(r.text)
    assert 'PREFIX' in r.text, repr(r.text)
    assert 'SUFFIX' in r.text, repr(r.text)

    # Do not destroy html tags due to encoding bugs
    r = HttpResponse("http://example.com", encoding='utf-8',
                     body=b'\xf0<span>value</span>')
    assert '<span>value</span>' in r.text, repr(r.text)


def test_html_encoding():
    body = b"""<html><head><title>Some page</title><meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
    </head><body>Price: \xa3100</body></html>'
    """
    r1 = HttpResponse("http://www.example.com", body=body)
    assert r1.encoding == 'cp1252'
    assert r1.text == body.decode('cp1252')

    body = b"""<?xml version="1.0" encoding="iso-8859-1"?>
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
    Price: \xa3100
    """
    r2 = HttpResponse("http://www.example.com", body=body)
    assert r2.encoding == 'cp1252'
    assert r2.text == body.decode('cp1252')


def test_html_headers_encoding_precedence():
    # for conflicting declarations headers must take precedence
    body = b"""<html><head><title>Some page</title><meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    </head><body>Price: \xa3100</body></html>'
    """
    response = HttpResponse("http://www.example.com", body=body,
                            headers={"Content-type": "text/html; charset=iso-8859-1"})
    assert response.encoding == 'cp1252'
    assert response.text == body.decode('cp1252')


def test_html5_meta_charset():
    body = b"""<html><head><meta charset="gb2312" /><title>Some page</title><body>bla bla</body>"""
    response = HttpResponse("http://www.example.com", body=body)
    assert response.encoding == 'gb18030'
    assert response.text == body.decode('gb18030')


def test_browser_html():
    src = "<html><body><p>Hello, </p><p>world!</p></body></html>"
    html = BrowserHtml(src)
    assert html == src
    assert html != "foo"

    assert html.xpath("//p/text()").getall() == ["Hello, ", "world!"]
    assert html.css("p::text").getall() == ["Hello, ", "world!"]
    assert isinstance(html.selector, parsel.Selector)
