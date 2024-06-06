from base64 import b64encode, b64decode
from gzip import decompress

from dom_tokenizers.pre_tokenizers.sniffer import (
    base64iness,
    _b64_shufflamap,
)
from .util import load_resource


LOREM_IPSUM_GZ = load_resource("lorem-ipsum.txt.gz", mode="rb")

HARD_BASE64 = b64encode(LOREM_IPSUM_GZ)
NOT_BASE64 = decompress(LOREM_IPSUM_GZ)
SOFT_BASE64 = b64encode(NOT_BASE64)  # harder to spot tho

HARD_BASE64, SOFT_BASE64, NOT_BASE64 = (
    x.decode("ascii")
    for x in (HARD_BASE64, SOFT_BASE64, NOT_BASE64))

NOT_BASE64 = "".join(
    c for c in NOT_BASE64.title() if c in _b64_shufflamap)



def test_scrunchiness():
    print(repr(HARD_BASE64)[:80])
    print(repr(SOFT_BASE64)[:80])
    print(repr(NOT_BASE64)[:80])
    print()
    print("SIZE HARD SOFT TEXT")
    print("-------------------")
    for shift in range(10, 2, -1):
        nbytes = 1 << shift
        print(f"{nbytes:>4}", " ".join(
            f"{base64iness(sample[:nbytes]):4.2f}"
            for sample in (HARD_BASE64, SOFT_BASE64, NOT_BASE64)))
    assert False
