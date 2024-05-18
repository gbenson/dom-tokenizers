import json

from datasets import Dataset

from dom_tokenizers.train import train_tokenizer

from .util import load_resource


def test_base64(dom_snapshot_pre_tokenizer):
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
    )
    tokenizer.backend_tokenizer.pre_tokenizer = dom_snapshot_pre_tokenizer

    tokens = tokenizer.tokenize(snapshot)
    print(tokens)

    # <img src="data:image/svg+xml;base64,PHN2Zy...2Zz4=" width="256"...
    expect = [
        "[TAG]", "img",
        "[ATTR]", "src",
        "data", "image", "svg", "xml", "base64", "[BASE64]", "svg",
        "[ATTR]", "width",
        "256",
    ]
    assert tokens.count("img") == 1
    start = tokens.index("img") - 1
    assert start > 0
    limit = start + len(expect)
    assert tokens[start:limit] == expect
