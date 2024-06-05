from dom_tokenizers.pre_tokenizers.splitter import TextSplitter

from .util import load_resource, json


def load_b64_miss(basename):
    return json.loads(load_resource(f"base64-misses/{basename}.json"))["text"]


def test_1655961866939():
    tokens = TextSplitter().split(load_b64_miss(1655961866939))
    assert "L0gH7uiS0HpxahWElsqTPIQS2YzobL" not in tokens
