import cProfile as profile
import os
import time
import warnings

from argparse import ArgumentParser
from hashlib import sha256

from datasets import load_dataset
from tokenizers import NormalizedString

from ..internal import json
from ..internal.transformers import AutoTokenizer
from ..pre_tokenizers import DOMSnapshotPreTokenizer
from .defaults import (
    DEFAULT_BASE_TOKENIZER,
    DEFAULT_SPLIT,
    SEND_BUGS_TO,
)

DEFAULT_STATS_FILENAME = f"{__name__.rsplit('.', 1)[-1]}.prof"
DEFAULT_CACHEDIR = os.path.join("~", ".cache", *(__name__.split(".")))


def profile_tokenizer(fp, pretokenize_dom):
    total_elapsed = 0
    for index, line in enumerate(fp.readlines()):
        line = line.rstrip()
        nbytes = len(line)
        start = time.perf_counter_ns()
        splits = pretokenize_dom(None, NormalizedString(line))
        elapsed = time.perf_counter_ns() - start
        total_elapsed += elapsed
        nsplits = len(splits)
        bps = nbytes / nsplits
        print(
            f"example {index+1:3}: {len(line):7} bytes ->"
            f" {len(splits):7} pre-tokens; {bps:4.1f} bytes/pre-token"
            f" in {elapsed*1e-6:9.3f} ms")
    print(
        f"--\n{index+1} examples processed in"
        f" {total_elapsed*1e-9:.2f} seconds")


def cache_filename_for(dataset, split=None, cachedir=DEFAULT_CACHEDIR):
    if os.path.exists(dataset):
        dataset = os.path.realpath(dataset)
    cache_key = (f"{dataset}\0{split or ''}").encode("utf-8")
    filename = f"{sha256(cache_key).hexdigest()}.jsonl"
    return os.path.join(os.path.expanduser(cachedir), filename)


def main():
    parser = ArgumentParser(
        description="Profile DOM-aware pre-tokenizers.",
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
        "-o", "--output", metavar="FILE", dest="stats_filename",
        default=DEFAULT_STATS_FILENAME,
        help=(f"file to write profiler statistics into "
              f" [default: {DEFAULT_STATS_FILENAME}]"))
    args = parser.parse_args()

    warnings.filterwarnings("ignore", message=r".*resume_download.*")

    cache_filename = cache_filename_for(args.dataset, args.split)
    if not os.path.exists(cache_filename):
        is_local = os.path.exists(args.dataset)
        training_dataset = load_dataset(
            args.dataset,
            split=args.split,
            streaming=not is_local)
        os.makedirs(os.path.dirname(cache_filename), exist_ok=True)
        with open(cache_filename, "w") as fp:
            for row in training_dataset:
                json.dump(row["dom_snapshot"], fp)
                fp.write("\n")
        del training_dataset

    base_tokenizer = AutoTokenizer.from_pretrained(args.base_tokenizer)
    DOMSnapshotPreTokenizer.hook_into(base_tokenizer)
    pre_tokenize_dom = base_tokenizer.dom_pre_tokenizer._pre_tokenize_dom

    with open(cache_filename) as fp:
        profile.runctx(
            "profile_tokenizer(fp, pre_tokenize_dom)",
            globals(), locals(), args.stats_filename)
    print(f'Now run "python -m pstats {args.stats_filename}"')
