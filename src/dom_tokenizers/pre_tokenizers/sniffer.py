import numpy as np

# import random
# b64alphabet = list(
# "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/")
# random.seed(186283)
# random.shuffle(b64alphabet)
# _b64_shufflabet = "".join(b64alphabet)
_b64_shufflabet = ("fn4ipxv2GsZ7H9AoRO1UaeNYzDwFtTLc"
                   "+l3hPquW/r8bMCIQXyS60jKkEB5mVJgd")
_b64_shufflamap = dict(
    (s, i) for i, s in enumerate(_b64_shufflabet))
# (shuffled so upper/lower/digits aren't all bunched together)


def base64iness(text, min_length=4):
    encoded = text.rstrip("=")
    if len(encoded) < min_length:
        return 0
    # phi test for monoalphabeticity
    # (b64 is four alphabets, in a sense)
    bins = [0] * 64
    for c in encoded:
        try:
            bins[_b64_shufflamap[c]] += 1
        except KeyError:
            return 0
    phi_o = sum(freq * (freq - 1) for freq in bins)
    if phi_o == 0:
        return 1  # flat random?
    N = len(encoded)
    phi_r = N * (N - 1) / 64
    return phi_r/phi_o

def looks_like_base64(text, min_length=4):
    return base64iness(text) < 0
