import json

from ...util import load_resource


def test_raw_response_unwrapping(pre_tokenizer):
    """Test that DOM snapshots wrapped in CDP browser responses are
    pretokenized identically to non-wrapped DOM snapshots like those
    in https://huggingface.co/datasets/gbenson/webui-dom-snapshots.
    """
    wrapped_snapshot = load_resource("raw-browser-response.json")
    browser_response = json.loads(wrapped_snapshot)
    assert set(browser_response.keys()) == {"id", "result", "sessionId"}
    regular_snapshot = browser_response["result"]
    assert set(regular_snapshot.keys()) == {"documents", "strings"}
    regular_snapshot = json.dumps(regular_snapshot, separators=(",", ":"))
    assert regular_snapshot in wrapped_snapshot
    del browser_response

    regular_tokens = pre_tokenizer.tokenize(regular_snapshot)
    assert regular_tokens.count("[TAG]") == 5
    assert regular_tokens.count("hello") == 2

    wrapped_tokens = pre_tokenizer.tokenize(wrapped_snapshot)
    assert wrapped_tokens == regular_tokens
