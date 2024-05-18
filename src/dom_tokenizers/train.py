import json
import os
import warnings

from argparse import ArgumentParser
from math import log10, floor

from datasets import load_dataset
from tokenizers.pre_tokenizers import WhitespaceSplit

from .tokenizers import DOMSnapshotTokenizer

DEFAULT_BASE_TOKENIZER = "bert-base-cased"
DEFAULT_SPLIT = "train"
DEFAULT_SIZE = 1024
SEND_BUGS_TO = "https://github.com/gbenson/dom-tokenizers/issues"


def train_tokenizer(
        training_dataset,
        base_tokenizer=DEFAULT_BASE_TOKENIZER,
        vocab_size=DEFAULT_SIZE,
        corpus_size=None):

    # Create the base tokenizer we'll train our new tokenizer from.
    if isinstance(base_tokenizer, str):
        base_tokenizer = DOMSnapshotTokenizer.from_pretrained(
            base_tokenizer)

    # It's not possible to train using a custom pre-tokenizer, the Rust
    # code raises "Exception: Custom PreTokenizer cannot be serialized"
    # (see https://github.com/huggingface/tokenizers/issues/269) so we
    # have to run our pre-tokenizer manually, then join its output with
    # whitespace and hope the regular pretokenizer takes it back apart
    # how we need it to.

    new_pretokenizer = base_tokenizer.backend_tokenizer.pre_tokenizer
    base_tokenizer.backend_tokenizer.pre_tokenizer = WhitespaceSplit()
    base_pretokenizer = base_tokenizer.backend_tokenizer.pre_tokenizer

    def futz_input(real_input):
        pretokenized = new_pretokenizer.pre_tokenize_str(real_input)
        want_tokens = [token for token, offsets in pretokenized]
        futzed_input = " ".join(want_tokens)
        pretokenized = base_pretokenizer.pre_tokenize_str(futzed_input)
        got_tokens = [token for token, offsets in pretokenized]
        assert got_tokens == want_tokens
        return futzed_input

    # List the custom special tokens that need adding to our tokenizer.
    dom_snapshot_pre_tokenizer = base_tokenizer.backend_pre_tokenizer
    new_special_tokens = [
        special_token
        for special_token in dom_snapshot_pre_tokenizer.special_tokens
        if base_tokenizer.tokenize(special_token) != [special_token]
    ]

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

    # Post-training fixups.
    new_tokenizer.name_or_path = _pretty_name(new_tokenizer)
    new_tokenizer.model_max_length = 1 << 27  # >128x the biggest I've seen
    for token in new_special_tokens:
        attr = f"{token[1:-1].lower()}_token"
        if not hasattr(new_tokenizer, attr):
            continue  # not a "special" special token
        if getattr(new_tokenizer, attr) is not None:
            continue  # already got this one
        setattr(new_tokenizer, attr, token)

    return new_tokenizer


def _save_directory_for(*args, **kwargs):
    wantdir = _pretty_name(*args, **kwargs)
    currdir = os.getcwd()
    if os.path.basename(currdir) == wantdir:
        return currdir
    return os.path.join(currdir, wantdir)


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
    parser = ArgumentParser(
        description="Train DOM-aware tokenizers.",
        epilog=f"Report bugs to: <{SEND_BUGS_TO}>.")
    parser.add_argument(
        "dataset", metavar="DATASET",
        help="dataset containing the training corpus")
    parser.add_argument(
        "--base-tokenizer", metavar="ID",
        default=DEFAULT_BASE_TOKENIZER,
        help=(f"tokenizer to train ours from"
              f" [default: {DEFAULT_BASE_TOKENIZER}]"))
    parser.add_argument(
        "-s", "--split", metavar="SPLIT", default=DEFAULT_SPLIT,
        help=(f"split of the training dataset to use"
              f" [default: {DEFAULT_SPLIT}]"))
    parser.add_argument(
        "-N", "--num-inputs", metavar="N", dest="corpus_size",
        type=int,
        help=("number of sequences in the training dataset, if known;"
              " this is used to provide meaningful progress tracking"))
    parser.add_argument(
        "-n", "--num-tokens", metavar="N", dest="vocab_size", type=int,
        default=DEFAULT_SIZE,
        help=(f"desired vocabulary size, including all special tokens and"
              f" the initial alphabet [default: {DEFAULT_SIZE} tokens]"))
    parser.add_argument(
        "-o", "--output", metavar="DIR", dest="save_directory",
        help=("directory to save the trained tokenizer into"
              " [default: something based on targeted vocabulary size]"))
    args = parser.parse_args()

    save_directory = args.save_directory
    if save_directory is None:
        save_directory = _save_directory_for(vocab_size=args.vocab_size)
        print(f"Output directory: {save_directory}\n")

    warnings.filterwarnings("ignore", message=r".*resume_download.*")

    tokenizer = train_tokenizer(
        load_dataset(
            args.dataset,
            split=args.split,
            streaming=True),
        base_tokenizer=args.base_tokenizer,
        vocab_size=args.vocab_size,
        corpus_size=args.corpus_size)
    print(f'\n{tokenizer.tokenize("training complete")}')

    tokenizer.save_pretrained(save_directory)

    print(tokenizer.tokenize("tokenizer state saved"))
    print(tokenizer.tokenize("see you soon") + ["!!"])
