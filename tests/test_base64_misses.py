from dom_tokenizers.pre_tokenizers.splitter import TextSplitter
from dom_tokenizers.pre_tokenizers.sniffer import base64iness

from .util import load_resource, json


def load_b64_miss(basename):
    return json.loads(load_resource(f"base64-misses/{basename}.json"))["text"]


def test_1655961866939():
    for token in TextSplitter().split(load_b64_miss(1655961866939)):
        print(f"{base64iness(token):4.1f}% {token}")
        assert token != "L0gH7uiS0HpxahWElsqTPIQS2YzobL"
