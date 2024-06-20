from base64 import b64decode as _b64decode, _bytes_from_decode_data, binascii

from vec64 import base64_symbol_indexes as _b64symvec


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


def b64symvec(text: str) -> bytes:
    try:
        return _b64symvec(text)
    except UnicodeEncodeError:
        return _b64symvec(text.encode(errors="replace"))


b64symvec.__doc__ = _b64symvec.__doc__
