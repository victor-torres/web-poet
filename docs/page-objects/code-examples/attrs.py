from attrs import define

from web_poet import HttpResponse, ItemPage, field


@define
class FooPage(ItemPage[dict]):
    response: HttpResponse

    @field
    def foo(self) -> str:
        return self.response.css(".foo").get()
