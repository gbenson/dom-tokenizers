import os
import sys

import pytest

from dom_tokenizers.scripts.profile import (
    main as profile_tokenizer,
    profile as profile_module,
)


@pytest.fixture
def test_dataset():
    try:
        return os.environ["TEST_DATASET"]
    except KeyError as e:
        pytest.skip(f"Set {e} to run this test")


def test_profile_tokenizer(test_dataset, monkeypatch, tmp_path):
    """Run `profile-tokenizer` like a user ran it, except not actually
    in the profiler, in order to flex all code paths used in tokenizing
    the specified dataset and have tham show up in the tests' coverage
    report.  `profile-tokenizer` sets everything up to sidestep the Rust
    layer so its not there to block everything beneath it from appearing
    in the profile and coverage reports.
    """

    def _runctx(cmd, _globals, _locals, filename=None):
        assert cmd == "profile_tokenizer(fp, pre_tokenize_dom)"
        exec(cmd, _globals, _locals)

    monkeypatch.setattr(profile_module, "runctx", _runctx)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", [sys.argv[0], test_dataset])
    profile_tokenizer()
