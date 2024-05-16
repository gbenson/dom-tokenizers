import pytest


class PreTokenizerTester:
    def __init__(self, pre_tokenizer):
        self.wrapped_pre_tokenizer = pre_tokenizer

    @property
    def pre_tokenize_str(self):
        return self.wrapped_pre_tokenizer.pre_tokenize_str

    def tokenize(self, *args, **kwargs):
        return [
            token
            for token, offsets in self.pre_tokenize_str(*args, **kwargs)
        ]


@pytest.fixture()
def pre_tokenizer(dom_snapshot_pre_tokenizer):
    return PreTokenizerTester(dom_snapshot_pre_tokenizer)
