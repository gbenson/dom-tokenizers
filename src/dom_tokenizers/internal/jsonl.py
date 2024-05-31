from datetime import datetime
from functools import cached_property
from typing import Optional

from . import json


class Writer:
    def __init__(
            self,
            filename: Optional[str] = None,
            *,
            mode: str = "a",
            basename: Optional[str] = None,
            ext: str = ".jsonl",
            with_timestamp: bool = False,
    ):
        if filename is None:
            filename = basename
            if with_timestamp:
                filename = f"{filename}-{datetime.now():%Y%m%d%H%M%S%f}"
            filename = f"{filename}{ext}"
        self.filename = filename
        self._mode = mode

    @cached_property
    def _fp(self):
        return open(self.filename, self._mode)

    def write(self, **fields):
        json.dump(fields, self._fp)
        self._fp.write("\n")
