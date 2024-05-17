import os

# Don't print "None of PyTorch, TensorFlow >= 2.0, or Flax have been
# found. Models won't be available and only tokenizers, configuration
# and file/data utilities can be used" warning.  Tokenizers is all we
# want!

__var_name = "TRANSFORMERS_NO_ADVISORY_WARNINGS"
__orig_val = os.environ.get(__var_name)
os.environ[__var_name] = "1"
try:
    from transformers import AutoTokenizer  # noqa: F401
finally:
    if __orig_val is None:
        os.environ.pop(__var_name)
    else:  # pragma: no cover
        os.environ[__var_name] = __orig_val
    del __var_name, __orig_val, os
