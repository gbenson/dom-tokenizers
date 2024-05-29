import json

from datasets import Dataset

from dom_tokenizers.train import train_tokenizer, DEFAULT_VOCAB_SIZE

from .util import load_resource


def test_base64(dom_snapshot_tokenizer):
    """Test that base64 is entered successfully.  Incorrectly-sequenced
    lowercasing (i.e. applied prior to pre-tokenization) will cause this
    test to fail.
    """
    snapshot = load_resource("svg-in-base64.json")
    tokenizer = train_tokenizer(
        training_dataset=Dataset.from_dict({
            "dom_snapshot": (
                json.loads(snapshot),
            ),
        }),
        base_tokenizer=dom_snapshot_tokenizer.name_or_path  # flex with string
    )
    assert tokenizer.vocab_size < DEFAULT_VOCAB_SIZE
    tokens = tokenizer.tokenize(snapshot)
    print(tokens)

    # <img src="data:image/svg+xml;base64,PHN2Zy...2Zz4=" width="256"...
    expect = [
        "<", "img",
        "_", "src", "=",
        "data", "image", "svg", "xml", "base64",
        "[BASE64]",
        "svg", "_", "width", "=",
        "256",
    ]
    assert tokens.count("img") == 1
    start = tokens.index("img") - 1
    assert start > 0
    limit = start + len(expect)
    assert tokens[start:limit] == expect


def test_xhtml(dom_snapshot_tokenizer, expect_lowercased_tokens):
    """Test that various weird XHTML things make it through the splitter.
    The first 100 or so tokens of this document flex almost every branch
    of the pre-tokenizer, including some edge cases we likely don't test
    elsewhere.
    """
    snapshot = load_resource("xhtml-1.0.json")
    max_vocab_size = 1500
    tokenizer = train_tokenizer(
        training_dataset=Dataset.from_dict({
            "dom_snapshot": (
                json.loads(snapshot),
            ),
        }),
        vocab_size=max_vocab_size,
        base_tokenizer=dom_snapshot_tokenizer,  # flex with prebuilt tokenizer
    )
    assert tokenizer.vocab_size > DEFAULT_VOCAB_SIZE
    assert tokenizer.vocab_size < max_vocab_size
    tokens = tokenizer.tokenize(snapshot)

    start = 0
    for expect in (
            # XML declaration which Chrome transformed into a comment
            ["<!--", "xml", "version", "1", "0", "encoding", "utf", "8",
             "-->"],

            # DTD
            ["<!DOCTYPE", "html", "PUBLIC", "W3C", "DTD", "XHTML", "1",
             "0", "Strict", "EN", "http", "www", "w3", "org", "TR",
             "xhtml1", "DTD", "xhtml1", "strict", "dtd", ">"],

            # Start tag with namespaced attributes
            ["<", "html", "_", "xmlns", "=", "http", "www", "w3", "org",
             "1999", "xhtml", "_", "lang", "=", "en", "_", "xml", "lang",
             "=", "en", "_", "slick", "uniqueid", "=", "3", ">"],

            # Start tag with no attributes
            ["<", "head", ">"],

            # Two empty element tags with regular attributes
            ["<", "meta", "_", "http", "equiv", "=", "Content", "Type",
             "_", "content", "=", "text", "html", "charset", "utf", "8",
             ">"],
            ["<", "meta", "_", "name", "=", "viewport", "_", "content",
             "=", "width", "device", "width", ">"],

            # The start and end tags of an element with some content
            ["<", "title", ">", "Inauspicious", "org", "</", "title", ">"],

            # A void element with a non-ASCII character in an attribute
            ["<", "meta", "_", "name", "=", "copyright", "_", "content",
             "=", "Copyright", "2017", "Gary", "Benson", ">"],
    ):
        limit = start + len(expect)
        if expect_lowercased_tokens:
            expect = [token.lower() for token in expect]
        assert tokens[start:limit] == expect
        start = limit

    # Check that no meta tag was ever closed
    meta_indexes = [
        index
        for index, token in enumerate(tokens)
        if token == "meta"
    ]
    assert meta_indexes == [60, 77, 98, 112]
    for index in meta_indexes:
        assert tokens[index - 1] == "<"
        assert tokens[index + 1] == "_"

    # Check the final tokens too, for broken end tags and whatnot.
    # There's an empty non-void element in here, div#entries, so
    # we get to check they're handling correctly too.
    expect = [
        "org",
        "</", "a", ">",
        "</", "p", ">",
        "</", "div", ">",
        "<", "div", "_", "id", "=", "entries", ">",
        "</", "div", ">",
        "<", "div", "_", "id", "=", "loadmore", ">",
        "Load", "more",
        "</", "div", ">",
        "</", "div", ">",
        "</", "body", ">",
        "</", "html", ">",
    ]
    if expect_lowercased_tokens:
        expect = [token.lower() for token in expect]
    assert tokens[-len(expect):] == expect
