import pytest

from dom_tokenizers.internal.transformers import AutoTokenizer
from dom_tokenizers.train import DEFAULT_BASE_TOKENIZER


@pytest.fixture
def base_tokenizer():
    yield AutoTokenizer.from_pretrained(DEFAULT_BASE_TOKENIZER)
