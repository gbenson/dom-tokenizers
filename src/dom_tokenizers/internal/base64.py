from base64 import b64decode as _b64decode, _bytes_from_decode_data, binascii

from vec64 import base64_symbol_indexes as _base64_symbol_indexes


def b64decode(s, *args, **kwargs) -> bytes:
    fix_padding = kwargs.pop("fix_padding", False)
    try:
        return _b64decode(s, *args, **kwargs)
    except binascii.Error:
        if not fix_padding:
            raise

    s = _bytes_from_decode_data(s)
    t = s.rstrip(b"=")
    n = len(t) & 3
    t += b"AA=="[n:]
    return _b64decode(t, *args, **kwargs)


def base64_symbol_indexes(text: str) -> bytes:
    try:
        return _base64_symbol_indexes(text)
    except UnicodeEncodeError:
        return _base64_symbol_indexes(text.encode(errors="replace"))


base64_symbol_indexes.__doc__ = _base64_symbol_indexes.__doc__
