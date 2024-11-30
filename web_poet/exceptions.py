class ReloadResponseData(Exception):
    """Indicates that there's something wrong with :class:`~.ResponseData` and
    it needs to be downloaded again.

    You should use this in instance where the HTTP Response is malformed, missing
    some required information, etc.

    This should be raised inside the subclasses of :class:`~.WebPage` or anything
    which requires :class:`~.ResponseData` as a dependency. The framework which
    handles the Page Objects should then attempt to create a new instance with a
    fresh :class:`~.ResponseData` dependency.
    """

    pass


class DelegateFallback(Exception):
    """Indicates that the Page Object isn't able to perform data extractions on
    a given page.

    This should be raised in cases wherein the page has unknown layouts, unsupported
    data, etc.

    Raising this won't be a guarantee that a fallback parser for the page is
    available. It would depend on the framework using the Page Object on how to
    resolve the fallbacks.
    """

    pass
