try:
    from itertools import batched
except ImportError:
    # Python < 3.12
    from itertools import pairwise, cycle

    def batched(p, n):
        if n != 2:
            raise ValueError(n)
        return (pair for pair, keep in zip(
            pairwise(p), cycle((True, False))) if keep)
