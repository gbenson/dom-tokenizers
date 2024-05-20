import json
import warnings

from argparse import ArgumentParser
from difflib import SequenceMatcher

from .tokenizers import DOMSnapshotTokenizer

SEND_BUGS_TO = "https://github.com/gbenson/dom-tokenizers/issues"


class TokenStreamDiffer:
    @classmethod
    def compare(cls, *args, **kwargs):
        return cls(*args, **kwargs)._compare()

    def __init__(self, a, b, ident=None):
        self.ident = ident
        self.a = a
        self.b = b
        self.header_printed = False

    def _compare(self):
        cruncher = SequenceMatcher(a=self.a, b=self.b)
        for tag, alo, ahi, blo, bhi in cruncher.get_opcodes():
            match tag:
                case "equal":
                    pass  # reset?
                case "insert":
                    for line in self._evaluate_change(
                            self.a, alo, ahi,
                            self.b, blo, bhi):
                        yield line
                case "replace":
                    for line in self._evaluate_change(
                            self.a, alo, ahi,
                            self.b, blo, bhi):
                        yield line
                case other:  # noqa: F841
                    raise NotImplementedError((tag, alo, ahi, blo, bhi))

    @staticmethod
    def _merge_partials(tokens, start, limit):
        if start == limit:
            return None
        tokens = tokens[start:limit]
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if not token.startswith("##"):
                i += 1
                continue
            assert i > 0
            tokens[i - 1] += tokens.pop(i)[2:]
        return tokens

    def _evaluate_change(self, a, astart, alimit, b, bstart, blimit):
        while astart and a[astart].startswith("##"):
            astart -= 1
            if bstart != blimit:
                if bstart:
                    bstart -= 1
                assert a[astart] == b[bstart]
        while bstart and b[bstart].startswith("##"):
            bstart -= 1
            if astart != alimit:
                if astart:
                    astart -= 1
                assert a[astart] == b[bstart]

        adbg = repr(a[astart:alimit])
        bdbg = repr(b[bstart:blimit])
        try:
            a = self._merge_partials(a, astart, alimit)
            b = self._merge_partials(b, bstart, blimit)
        except AssertionError:
            yield f"-{adbg}"
            yield f"+{bdbg}"
            raise

        if not self.header_printed:
            yield f"\x1B[38;5;220m{self.ident}:\x1B[0m"
            self.header_printed = True

        if a:
            yield f"\x1B[31m-{' '.join(a)}\x1B[0m"
        if b:
            yield f"\x1B[32m+{' '.join(b)}\x1B[0m"


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
        for line in TokenStreamDiffer.compare(a, b, source_index):
            print(line)
