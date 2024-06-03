from base64 import b64decode, b64encode
from enum import Enum, auto
from typing import Optional


class FileType(Enum):
    GIF = auto()
    PNG = auto()
    RIFF = auto()
    SVG = auto()
    WEBP = auto()
    WOFF = auto()


MIN_BYTES_FOR_SNIFF = 33  # Smallest I've seen was a 35 byte GIF
MIN_BASE64_FOR_SNIFF = (MIN_BYTES_FOR_SNIFF * 8) // 6

_MAGIC = {
    "GIF": b"GIF8",
    "PNG": b"\x89PNG",
    "RIFF": b"RIFF",
    "SVG": b"<svg",
    "WOFF": b"wOFF",
}

MAGIC = dict(
    (magic, getattr(FileType, typename))
    for typename, magic in _MAGIC.items()
)

BASE64_MAGIC = dict(
    (b64encode(magic)[:5].decode("ascii"), filetype)
    for magic, filetype in MAGIC.items()
)

_RIFF_MAGIC = {
    "WEBP",
}

RIFF_MAGIC = dict(
    (code.encode("ascii"), getattr(FileType, code))
    for code in _RIFF_MAGIC
)


def sniff_base64(encoded: str) -> Optional[FileType]:
    if len(encoded) < MIN_BASE64_FOR_SNIFF:
        return None
    filetype = BASE64_MAGIC.get(encoded[:5])
    if filetype != FileType.RIFF:
        return filetype
    return RIFF_MAGIC.get(b64decode(encoded[:16])[-4:])


def sniff_bytes(data: bytes) -> Optional[FileType]:
    if len(data) < MIN_BYTES_FOR_SNIFF:
        return None
    filetype = MAGIC.get(data[:4])
    if filetype != FileType.RIFF:
        return filetype
    return RIFF_MAGIC.get(data[8:12])
