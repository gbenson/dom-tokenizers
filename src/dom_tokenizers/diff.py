import json
import warnings

from argparse import ArgumentParser
from difflib import unified_diff

from .tokenizers import DOMSnapshotTokenizer

SEND_BUGS_TO = "https://github.com/gbenson/dom-tokenizers/issues"


def main():
    parser = ArgumentParser(
        description="Compare saved tokenizations with specified tokenizer's.",
        epilog=f"Report bugs to: <{SEND_BUGS_TO}>.")

    parser.add_argument(
        "reference", metavar="FILENAME",
        help="output from dump-tokenizers")
    parser.add_argument(
        "tokenizer", metavar="TOKENIZER",
        help="tokenizer model name or path")
    args = parser.parse_args()

    warnings.filterwarnings("ignore", message=r".*resume_download.*")

    tokenizer = DOMSnapshotTokenizer.from_pretrained(args.tokenizer)
    assert tokenizer.backend_tokenizer.normalizer.strip_accents

    for line in open(args.reference).readlines():
        row = json.loads(line)
        source_index = row["source_index"]
        serialized = json.dumps(row["dom_snapshot"], separators=(",", ":"))
        b = tokenizer.tokenize(serialized)
        a = row["tokenized"]
        if b == a:
            continue
        for line in unified_diff(
                a, b,
                fromfile=f"a/{source_index}",
                tofile=f"b/{source_index}"):
            print(line.rstrip())
