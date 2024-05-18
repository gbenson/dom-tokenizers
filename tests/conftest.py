import pytest

from dom_tokenizers import DOMSnapshotTokenizer
from dom_tokenizers.train import DEFAULT_BASE_TOKENIZER


@pytest.fixture
def dom_snapshot_tokenizer():
    """An instance of a tokenizer that consumes JSON-serialized
    DOM snapshots.
    """
    return DOMSnapshotTokenizer.from_pretrained(DEFAULT_BASE_TOKENIZER)


@pytest.fixture
def dom_snapshot_pre_tokenizer(dom_snapshot_tokenizer):
    """An instance of a pre-tokenizer that consumes JSON-serialized
    DOM snapshots.
    """
    return dom_snapshot_tokenizer.backend_tokenizer.pre_tokenizer
