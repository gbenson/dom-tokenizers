from base64 import b64decode, b64encode
from enum import Enum, auto
from typing import Optional


class FileType(Enum):
    GIF = auto()
    PNG = auto()
    RIFF = auto()
    SVG = auto()
    WEBP = auto()


_MAGIC = {
    "GIF": b"GIF8",
    "PNG": b"\x89PNG",
    "RIFF": b"RIFF",
    "SVG": b"<svg",
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
    filetype = BASE64_MAGIC.get(encoded[:5])
    if filetype != FileType.RIFF:
        return filetype
    return RIFF_MAGIC.get(b64decode(encoded[:16])[-4:])
