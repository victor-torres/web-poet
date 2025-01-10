from .fields import Unset, UnsetType, field, item_from_fields, item_from_fields_sync
from .page_inputs import (
    AnyResponse,
    BrowserHtml,
    BrowserResponse,
    HttpClient,
    HttpRequest,
    HttpRequestBody,
    HttpRequestHeaders,
    HttpResponse,
    HttpResponseBody,
    HttpResponseHeaders,
    PageParams,
    RequestUrl,
    ResponseUrl,
    Stats,
)
from .pages import (
    Extractor,
    Injectable,
    ItemPage,
    ItemWebPage,
    Returns,
    SelectorExtractor,
    WebPage,
    validates_input,
)
from .requests import request_downloader_var
from .rules import (
    ApplyRule,
    OverrideRule,
    PageObjectRegistry,
    RulesRegistry,
    consume_modules,
)
from .utils import cached_method

default_registry = RulesRegistry()
handle_urls = default_registry.handle_urls
