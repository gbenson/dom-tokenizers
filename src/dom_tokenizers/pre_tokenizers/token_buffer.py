from collections.abc import Iterable

from tokenizers import NormalizedString


class TokenBuffer:
    def __init__(self):
        self._buf = []

    @property
    def tokens(self) -> list[NormalizedString]:
        return self._buf

    def append(self, token: str | NormalizedString):
        if not isinstance(token, NormalizedString):
            token = NormalizedString(token)
        self._buf.append(token)

    def extend(self, tokens: Iterable[str | NormalizedString]):
        for token in tokens:
            self.append(token)
