import pytest

from dom_tokenizers import DOMSnapshotPreTokenizer
from dom_tokenizers.internal.transformers import AutoTokenizer
from dom_tokenizers.train import DEFAULT_BASE_TOKENIZER


@pytest.fixture
def dom_snapshot_tokenizer():
    """An instance of a tokenizer that consumes JSON-serialized
    DOM snapshots.
    """
    tokenizer = AutoTokenizer.from_pretrained(DEFAULT_BASE_TOKENIZER)
    DOMSnapshotPreTokenizer.hook_into(tokenizer)
    return tokenizer


@pytest.fixture
def dom_snapshot_pre_tokenizer(dom_snapshot_tokenizer):
    """An instance of a pre-tokenizer that consumes JSON-serialized
    DOM snapshots.
    """
    return dom_snapshot_tokenizer.backend_tokenizer.pre_tokenizer
