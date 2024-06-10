import warnings

from argparse import ArgumentParser

from datasets import load_dataset

from ..internal import json
from ..internal.transformers import AutoTokenizer
from ..pre_tokenizers import DOMSnapshotPreTokenizer
from .defaults import (
    DEFAULT_BASE_TOKENIZER as DEFAULT_TOKENIZER,
    DEFAULT_SPLIT,
    SEND_BUGS_TO,
)


def main():
    parser = ArgumentParser(
        description="Output any dataset rows that break the tokenizer",
        epilog=f"Report bugs to: <{SEND_BUGS_TO}>.")
    parser.add_argument(
        "dataset", metavar="DATASET",
        help="dataset to tokenize.")
    parser.add_argument(
        "-s", "--split", metavar="SPLIT", default=DEFAULT_SPLIT,
        help=f"split of the dataset to tokenize [default: {DEFAULT_SPLIT}]")
    parser.add_argument(
        "-t", "--tokenizer", metavar="TOKENIZER", default=DEFAULT_TOKENIZER,
        help=f"tokenizer model name or path [default: {DEFAULT_TOKENIZER}]")
    args = parser.parse_args()

    warnings.filterwarnings("ignore", message=r".*resume_download.*")

    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer)
    tokenizer.model_max_length = 1 << 27
    DOMSnapshotPreTokenizer.hook_into(tokenizer)

    def is_breaking_row(row):
        tokenizer_input = json.dumps(row["dom_snapshot"])
        try:
            _ = tokenizer.tokenize(tokenizer_input)
        except Exception:
            return True
        return False

    dataset = load_dataset(args.dataset, split=args.split)
    dataset = dataset.filter(is_breaking_row)
    got_rows = dataset.num_rows
    print(f"Got {got_rows} breaking input{'' if got_rows == 1 else 's'}")
    if got_rows:
        dataset.to_parquet("breaking-inputs.parquet")
