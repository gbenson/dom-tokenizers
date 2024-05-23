# https://html.spec.whatwg.org/multipage/syntax.html#void-elements
VOID_ELEMENTS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "source",
    "track",
    "wbr",
}


def is_void_element(tag: str) -> bool:
    return tag.lower() in VOID_ELEMENTS
