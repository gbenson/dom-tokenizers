import os
import json
import warnings

from argparse import ArgumentParser
from math import log10, floor

from datasets import load_dataset
from tokenizers.pre_tokenizers import PreTokenizer, WhitespaceSplit

os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = str(True)
from transformers import AutoTokenizer

from .pre_tokenizers import DOMSnapshotPreTokenizer

DEFAULT_BASE = "bert-base-uncased"
DEFAULT_SPLIT = "train"
DEFAULT_SIZE = 1024
SEND_BUGS_TO = "https://github.com/gbenson/dom-tokenizers/issues"


def train_tokenizer(
        training_dataset,
        base_tokenizer=DEFAULT_BASE,
        vocab_size=DEFAULT_SIZE,
        corpus_size=None):

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

    # Try and get a dataset length, for the progress tracker.
    if corpus_size is None:
        try:
            corpus_size = len(training_dataset)
        except TypeError:
            pass
    cs = f"{corpus_size:,}" if corpus_size else "an unknown number of"
    print(f"Generating {vocab_size:,} tokens from {cs} examples:")

    # Train the new tokenizer.
    new_tokenizer = base_tokenizer.train_new_from_iterator(
        text_iterator=get_training_corpus(),
        vocab_size=vocab_size,
        new_special_tokens=new_special_tokens,
        length=corpus_size,
        show_progress=True,
    )
    new_tokenizer.name_or_path = _pretty_name(new_tokenizer)

    return new_tokenizer


def _pretty_name(tokenizer=None, *, vocab_size=None, prefix="dom-tokenizer-"):
    if vocab_size is None:
        vocab_size = tokenizer.vocab_size
    pretty_size = _round_and_prefix(vocab_size)
    return f"{prefix}{pretty_size}"


def _round_and_prefix(value):
    """314159 -> '314k'."""
    whole, frac = divmod(log10(value), 1)
    unit_index, whole = divmod(floor(whole), 3)
    value = round(10 ** (whole + frac))
    unit = ([""] + list("kMBTQ"))[unit_index]
    return f"{value}{unit}"


def main():
    p = ArgumentParser(
        description="Train DOM-aware tokenizers.",
        epilog=f"Report bugs to: <{SEND_BUGS_TO}>.")
    p.add_argument(
        "dataset", metavar="DATASET",
        help="dataset containing the training corpus")
    p.add_argument(
        "--base-tokenizer", metavar="ID", default=DEFAULT_BASE,
        help=f"tokenizer to train ours from [default: {DEFAULT_BASE}]")
    p.add_argument(
        "--split", default=DEFAULT_SPLIT, metavar="SPLIT", dest="split_name",
        help=(f"split of the training dataset to use"
              f" [default: {DEFAULT_SPLIT}]"))
    p.add_argument(
        "-N", "--num-inputs", metavar="N", dest="corpus_size",
        type=int,
        help=("number of sequences in the training dataset, if known;"
              " this is used to provide meaningful progress tracking"))
    p.add_argument(
        "-n", "--num-tokens", metavar="N", dest="vocab_size", type=int,
        default=DEFAULT_SIZE,
        help=(f"desired vocabulary size, including all special tokens and"
              f" the initial alphabet [default: {DEFAULT_SIZE} tokens]"))
    p.add_argument(
        "-o", "--output", metavar="DIR", dest="save_directory",
        help=("directory to save the trained tokenizer into"
              " [default: something based on targeted vocabulary size]"))
    args = p.parse_args()

    save_directory = args.save_directory
    if save_directory is None:
        save_directory = _pretty_name(vocab_size=args.vocab_size)
        print(f"Output directory: {save_directory}\n")

    warnings.filterwarnings("ignore", message=r".*resume_download.*")

    tokenizer = train_tokenizer(
        load_dataset(
            args.dataset,
            split=args.split_name,
            streaming=True),
        base_tokenizer=args.base_tokenizer,
        vocab_size=args.vocab_size,
        corpus_size=args.corpus_size)
    print(f'\n{tokenizer.tokenize("training complete")}')

    tokenizer.save_pretrained(save_directory)

    print(tokenizer.tokenize("tokenizer state saved"))
    print(tokenizer.tokenize("see you soon") + ["!!"])
