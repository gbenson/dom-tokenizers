import pytest

@pytest.mark.parametrize(
    "input_pair,expect_encoding",
    (("AA",  0*64  + 0),
     # ..
     ("/A",  0*64 + 63),
     ("AB",  1*64 +  0),
     # ..
     ("/B",  1*64 + 63),
     # ..
     ("A/", 63*64 +  0),
     # ..
     ("//", 63*64 + 63),
     ("A=", 64*64 +  0),
     # ..
     ("/=", 64*64 + 63),
     ("==", 64*64 + 64),
     # ...and:
     ("Cj", 35*64 +  3),
     ("o=", 64*64 + 40),
     ))
def test_pair_encoding(input_text, expect_output):
    pass


@pytest.mark.parametrize(
    "input_text,expect_output",
    (("Cjwvc3ZnPgo=",  # even
      (("Cj", "wv", "c3", "Zn", "Pg", "o="),
       ("jw", "vc", "3Z", "nP", "go"))),
     ("Cjwvc3ZnPg=",   # odd
      (("Cj", "wv", "c3", "Zn", "Pg"),
       ("jw", "vc", "3Z", "nP", "g="))),
     ))
def test_input_pairs(input_text, expect_output):
    pass
