import pytest

from tokenizers.pre_tokenizers import PreTokenizer

from dom_tokenizers.internal.transformers import AutoTokenizer
from dom_tokenizers.pre_tokenizers import DOMSnapshotPreTokenizer
from dom_tokenizers.train import DEFAULT_BASE_TOKENIZER


@pytest.fixture
def base_tokenizer():
    """An instance of the default base tokenizer we train our
    tokenizers from.
    """
    return AutoTokenizer.from_pretrained(DEFAULT_BASE_TOKENIZER)


@pytest.fixture
def dom_snapshot_pre_tokenizer():
    """An instance of a pre-tokenizer that consumes JSON-serialized
    DOM snapshots.
    """
    return PreTokenizer.custom(DOMSnapshotPreTokenizer())
