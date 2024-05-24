import pytest

from dom_tokenizers import DOMSnapshotPreTokenizer
from dom_tokenizers.internal.transformers import AutoTokenizer
from dom_tokenizers.train import DEFAULT_BASE_TOKENIZER


@pytest.fixture(params=list(sorted({
    "bert-base-uncased",
    "bert-base-cased",
    DEFAULT_BASE_TOKENIZER,
})))
def dom_snapshot_tokenizer(request):
    """An instance of a tokenizer that consumes JSON-serialized
    DOM snapshots.
    """
    tokenizer = AutoTokenizer.from_pretrained(request.param)
    DOMSnapshotPreTokenizer.hook_into(tokenizer)
    return tokenizer


@pytest.fixture
def dom_snapshot_pre_tokenizer(dom_snapshot_tokenizer):
    """An instance of a pre-tokenizer that consumes JSON-serialized
    DOM snapshots.
    """
    return dom_snapshot_tokenizer.backend_tokenizer.pre_tokenizer


@pytest.fixture
def expect_lowercased_tokens(dom_snapshot_tokenizer):
    """True if `dom_snapshot_tokenizer` should be emit no uppercase,
    False otherwise.
    """
    return dom_snapshot_tokenizer.do_lower_case
