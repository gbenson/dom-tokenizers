import warnings

from argparse import ArgumentParser

from datasets import load_dataset

from ..internal import json
from ..internal.transformers import AutoTokenizer
from ..pre_tokenizers import DOMSnapshotPreTokenizer
from .defaults import (
    DEFAULT_DATASET,
    DEFAULT_SPLIT,
    SEND_BUGS_TO,
)


def main():
    parser = ArgumentParser(
        description="Dump all tokenizations of a dataset.",
        epilog=f"Report bugs to: <{SEND_BUGS_TO}>.")
    parser.add_argument(
        "tokenizer", metavar="TOKENIZER",
        help="tokenizer model name or path")
    parser.add_argument(
        "-d", "--dataset", metavar="DATASET", default=DEFAULT_DATASET,
        help=f"dataset to tokenize [default: {DEFAULT_DATASET}]")
    parser.add_argument(
        "-s", "--split", metavar="SPLIT", default=DEFAULT_SPLIT,
        help=f"split of the dataset to tokenize [default: {DEFAULT_SPLIT}]")
    args = parser.parse_args()

    warnings.filterwarnings("ignore", message=r".*resume_download.*")

    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer)
    DOMSnapshotPreTokenizer.hook_into(tokenizer)

    dataset = load_dataset(args.dataset, split=args.split)
    rows = ((row["source_index"], row["dom_snapshot"]) for row in dataset)
    rows = ((si, ss, json.dumps(ss)) for si, ss in rows)
    rows = ((len(ser), si, ss, ser) for si, ss, ser in rows)
    for _, source_index, dom_snapshot, serialized in sorted(rows):
        print(json.dumps(dict(
            source_index=source_index,
            dom_snapshot=dom_snapshot,
            tokenized=tokenizer.tokenize(serialized)
        )))
