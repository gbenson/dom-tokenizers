from typing import Optional


class B64SkewCalculator:
    def __init__(self, ranges=("AZ", "az", "09"), extras="/+"):
        bins = [
            "".join(map(chr, range(start, stop + 1)))
            for start, stop in (
                    map(ord, start_stop)
                    for start_stop in ranges
            )
        ]
        if extras:
            bins.append(extras)

        self._num_bins = len(bins)
        self._char_bins = {}
        for bin_index, bin_chars in enumerate(bins):
            for c in bin_chars:
                self._char_bins[c] = bin_index

        alphabet_size = len(self._char_bins)
        self._expectations = [len(b) / alphabet_size for b in bins]

    def __call__(self, text: str) -> Optional[float]:
        """Return a value indicating how different `text` appears
        compared with base64-encoded random data, with zero being
        "this looks exactly like base64-encoded random data", and
        None being "it's not possible to decide".
        """
        if not text:
            return None
        counts = [0] * self._num_bins
        try:
            for c in text:
                counts[self._char_bins[c]] += 1
        except KeyError:
            return None  # invalid character

        normalized = 1 / len(text)
        return max(
            abs(normalized * count - expectation)
            for count, expectation in zip(counts, self._expectations)
        )


base64_skew = B64SkewCalculator(extras=None)


def base64_probability(text: str) -> float:
    """Return a value indicating how closely `text` resembles base64-
    encoded random data, with 1 being "exactly like it" and 0 being
    "100% not it".
    """
    skew = base64_skew(text)
    if not skew:
        return 0
    return 1 - skew
