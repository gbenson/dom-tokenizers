import os
import pickle
import re
import time

from collections import defaultdict, Counter
from itertools import chain, pairwise

from datasets import load_dataset
from vec64 import base64_symbol_indexes as vectorize

SOURCE_DATASET = "gbenson/webui-tokens-unlabelled"

# XXX update label-base64-tokens with this and the x264 below
_SPLITTER_FAIL_RE = re.compile(r"^(?:x|[uU]00)(?:2[267]|3[cC]|64)")


def all_texts(rows):
    for row in rows:
        text = row["text"]
        while (match := _SPLITTER_FAIL_RE.match(text)):
            if text.startswith("x264"):
                break
            yield text
            text = text[len(match.group(0)):]
            if not text:
                break
        if not text:
            continue
        yield text


def _load_all_texts():
    cache = os.path.expanduser("~/.cache/webui_tokens_unlabelled.pickle")
    if os.path.exists(cache):
        with open(cache, "rb") as fp:
            return pickle.load(fp)
    texts = list(all_texts(load_dataset(SOURCE_DATASET, split="train")))
    with open(cache, "wb") as fp:
        pickle.dump(texts, fp)
    return texts


def load_all_texts():
    inputs = _load_all_texts()
    print("Got", len(inputs), "inputs")
    return inputs


def winnow(inputs, limit=1):
    bins = defaultdict(list)
    for text in inputs:
        bins[text[:limit]].append(text)

    # Multiple bins mean we've not yet found one shared prefix.
    if len(bins) != 1:
        next_limit = limit + 1
        for next_inputs in bins.values():
            for text in winnow(next_inputs, next_limit):
                yield text
        return

    # One item in one bin means this input is unique.
    # Two items *might* be one with an '=' or '==', but, whatever?XXX
    inputs = next(iter(bins.values()))
    if len(inputs) > 4:
        inputs = list(sorted(inputs))
        lengths = [len(text) for text in inputs]
        shortest, longest = min(lengths), max(lengths)
        if lengths == list(range(shortest, longest + 1)):
            longest_text = inputs[-1]
            for text in inputs[:-1]:
                if not longest_text.startswith(text):
                    break
            else:
                return

    # Not a pyramid
    for text in inputs:
        yield text

def main():
    inputs = set()
    for text in load_all_texts():
        inputs.update(text.split("'"))
    print("Got", len(inputs), "unique inputs")
    inputs = set(winnow(inputs))
    print("Got", len(inputs), "winnowed inputs")
    start = time.time()
    hist = Counter(chain.from_iterable(
        ((b << 6) | a for a, b in pairwise(v))
        for v in map(vectorize, inputs)))
    elapsed = time.time() - start
    print("Counting", hist.total(), "pairs took", elapsed, "seconds")
    for pair, count in sorted(hist.items()):
        print(f"{pair:4} {count}")

