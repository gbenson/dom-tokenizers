import json
import warnings

from datasets import load_dataset
from tokenizers.pre_tokenizers import PreTokenizer, WhitespaceSplit
from transformers import AutoTokenizer

from .pre_tokenizers import DOMSnapshotPreTokenizer

FULL_DATASET = "gbenson/webui-dom-snapshots"
TEST_DATASET = "gbenson/interesting-dom-snapshots"


def train_tokenizer(
        *args,
        training_dataset=None,
        base_tokenizer="bert-base-uncased",
        vocab_size=1024,  # XXX including all tokens and alphabet
        **kwargs):
    """
    XXX
    base_tokenizer
    all other args passed to load_dataset for XXX...
    """

    # Load the training data we'll train our new tokenizer with.
    if training_dataset is None:
        training_dataset = load_dataset(*args, **kwargs)

    # Create the base tokenizer we'll train our new tokenizer from.
    if isinstance(base_tokenizer, str):
        base_tokenizer = AutoTokenizer.from_pretrained(base_tokenizer)

    # Create the custom pretokenizer our new tokenizer will use.
    new_pretokenizer = DOMSnapshotPreTokenizer()

    # List the custom special tokens that need adding to our tokenizer.
    new_special_tokens = [
        special_token
        for special_token in new_pretokenizer.special_tokens
        if base_tokenizer.tokenize(special_token) != [special_token]
    ]

    # It's not possible to train using a custom pre-tokenizer, the Rust
    # code raises "Exception: Custom PreTokenizer cannot be serialized"
    # (see https://github.com/huggingface/tokenizers/issues/269) so we
    # have to run our pre-tokenizer manually, then join its output with
    # whitespace and hope the regular pretokenizer takes it back apart
    # how we need it to.

    base_tokenizer.backend_tokenizer.pre_tokenizer = WhitespaceSplit()
    base_pretokenizer = base_tokenizer.backend_tokenizer.pre_tokenizer
    new_pretokenizer = PreTokenizer.custom(new_pretokenizer)

    def futz_input(real_input):
        pretokenized = new_pretokenizer.pre_tokenize_str(real_input)
        want_tokens = [token for token, offsets in pretokenized]
        futzed_input = " ".join(want_tokens)
        pretokenized = base_pretokenizer.pre_tokenize_str(futzed_input)
        got_tokens = [token for token, offsets in pretokenized]
        assert got_tokens == want_tokens
        return futzed_input

    def get_training_corpus():
        for row in training_dataset:
            yield futz_input(json.dumps(row["dom_snapshot"]))

    # Train the new tokenizer.
    new_tokenizer = base_tokenizer.train_new_from_iterator(
        text_iterator=get_training_corpus(),
        vocab_size=vocab_size,
        new_special_tokens=new_special_tokens,
        length=len(training_dataset),  # used for progress tracking
        show_progress=True,
    )

    return new_tokenizer


def main(save_directory="pretrained", use_full_dataset=False):
    warnings.filterwarnings("ignore", message=r".*resume_download.*")

    if use_full_dataset:
        dataset, kwargs = FULL_DATASET, dict(streaming=True)
    else:
        dataset, kwargs = TEST_DATASET, {}

    tokenizer = train_tokenizer(dataset, split="train", **kwargs)
    tokenizer.save_pretrained(save_directory)
