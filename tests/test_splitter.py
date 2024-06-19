import pytest

from dom_tokenizers.pre_tokenizers.splitter import TextSplitter, SPLIT


@pytest.mark.parametrize(
    "text,expect_splits",
    (("hello world", ["hello", " ", "world"]),
     ("$hello world", ["", "$", "hello", " ", "world"]),
     ("hello-world", ["hello", "-", "world"]),
     ("hello_world", ["hello_world"]),  # "\w" includes "_"
     ("@hello_world@", ["", "@", "hello_world", "@", ""]),
     (r'hello"world', ["hello", '"', "world"]),
     ("hello'world", ["hello'world"]),
     (r"hello\x3world", ["hello", "\\", "x3world"]),
     (r"hello\xcworld", ["hello", "\\", "xcworld"]),
     (r"hello\x3cworld", ["hello", "\\", "x3cworld"]),
     (r"hello^\x3cworld", ["hello", "^\\", "x3cworld"]),
     (r"hello\ueworld", ["hello", "\\", "ueworld"]),
     (r"hello\u7eworld", ["hello", "\\", "u7eworld"]),
     (r"hello\u07eworld", ["hello", "\\", "u07eworld"]),
     (r"hello\u007eworld", ["hello", "\\", "u007eworld"]),
     (r"hello@\u007eworld", ["hello", "@\\", "u007eworld"]),
     (r'hello\"world', ["hello", '\\"', "world"]),
     (r"hello\'world", ["hello", "\\", "'world"]),
     (r"hello\world", ["hello", "\\", "world"]),
     (r"hello\\world", ["hello", r"\\", "world"]),
     (r"hello&\world", ["hello", "&\\", "world"]),
     (r"hello&\\world", ["hello", r"&\\", "world"]),
     ("hello%26world", ["hello", "%", "26world"]),
     ("hello%260world", ["hello", "%", "260world"]),
     ("hello%2c0world", ["hello", "%", "2c0world"]),
     ("hello%2cworld", ["hello", "%", "2cworld"]),
     ("hello%%2cworld", ["hello", "%%", "2cworld"]),
     ("hello&amp;world", ["hello", "&", "amp", ";", "world"]),
     ("hello&quot;world", ["hello", "&", "quot", ";", "world"]),
     ("hello&gt;world", ["hello", "&", "gt", ";", "world"]),
     ("hello&lt;world", ["hello", "&", "lt", ";", "world"]),
     ("hello&apos;world", ["hello", "&", "apos", ";", "world"]),
     ("hello&xox;world", ["hello", "&", "xox", ";", "world"]),
     ("hello#&xox;world", ["hello", "#&", "xox", ";", "world"]),
     ("hello&9;world", ["hello", "&", "9", ";", "world"]),
     ("hello&#9;world", ["hello", "&#", "9", ";", "world"]),
     ("hello&#a;world", ["hello", "&#", "a", ";", "world"]),
     ("hello&#xa;world", ["hello", "&#", "xa", ";", "world"]),
     ("hello$&#xa;world", ["hello", "$&#", "xa", ";", "world"]),
     ("aGVsbG9+d29ybGQK", ["aGVsbG9+d29ybGQK"]),
     ("aGVsbG8sIHdvcmxkCg==", ["aGVsbG8sIHdvcmxkCg=="]),
     ("aGVsbG8sIHd+cmxkCg==", ["aGVsbG8sIHd+cmxkCg=="]),
     ))
def test_first_split_re(text, expect_splits):
    """Check that `TextSplitter.FIRST_SPLIT_RE` does what it should.
    """
    assert TextSplitter.FIRST_SPLIT_RE.split(text) == expect_splits


@pytest.mark.parametrize(
    "text,expect_tokens",
    (("hello world", ["hello", "world"]),
     ("hello-world", ["hello", "world"]),
     ("hello_world", ["hello", "world"]),

     # Javascript backslash escapes
     (r"hello\bworld", ["hello", "world"]),
     (r"hello\fworld", ["hello", "world"]),
     (r"hello\nworld", ["hello", "world"]),
     (r"hello\rworld", ["hello", "world"]),
     (r"hello\tworld", ["hello", "world"]),
     (r"hello\vworld", ["hello", "world"]),
     (r"hello\0world", ["hello", "world"]),
     (r"hello\'world", ["hello'world"]),
     (r'hello\"world', ["hello", "world"]),
     (r"hello\world", ["hello", "world"]),  # not valid => not handled
     ("hello\\", ["hello"]),
     ("\\hello", ["hello"]),
     ("_ \\_", []),
     ("_ \\_a", ["a"]),
     ("_ \\_ b", ["b"]),

     # Javascript unicode escapes
     (r"hello\u0020world", ["hello", "world"]),
     (r"hello\u020world", ["hello", "u020world"]),
     (r"hello\u20world", ["hello", "u20world"]),
     (r"hello\u9world", ["hello", "u9world"]),
     (r"hell\u006f\u020\u0077orld", ["hello", "u020world"]),  # mixd {,in}valid
     (r"hello\'\u0020world", ["hello", "world"]),
     # XXX N.B. Javascript is UTF-16 internal, so, surrogates?
     (r"\\u0041", ["A"]),
     (r"\\u0042\u0043", ["BC"]),
     (r"\u0044\\u0045", ["DE"]),

     # Javascript hex escapes
     (r"hello\x20world", ["hello", "world"]),
     (r"hello\x2world", ["hello", "x2world"]),  # not a valid \x escape
     (r"hello\xworld", ["hello", "xworld"]),  # ditto
     (r"hell\x6f\x9\x77orld", ["hello", "x9world"]),  # mixed {,in}valid
     (r"hello\xc2\x20world", ["helloA", "world"]),  # *not* utf-8
     (r"hell\'\u006f\x20world", ["hell'o", "world"]),
     (r'hello\"\x77orld', ["hello", "world"]),

     # Javascript octal escapes (no longer valid?)
     # (r"hello\40world", ["hello", "world"]),
     # (r"hello\040world", ["hello", "world"]),

     # HTML entities
     (r"hello&#32;world", ["hello", "world"]),
     (r"hello&#x20;world", ["hello", "world"]),
     (r"hello&apos;world", ["hello'world"]),
     (r"hello&quot;world", ["hello", "world"]),
     (r"hello&nbsp;world", ["hello", "world"]),
     (r"hello&#160;world", ["hello", "world"]),
     (r"hello&lt;world", ["hello", "world"]),
     (r"hello&gt;world", ["hello", "world"]),
     (r"hello&#X27;world", ["hello'world"]),
     (r"hello&#39;world", ["hello'world"]),
     (r"hell&#111;&#32;&#x77;orld", ["hello", "world"]),
     (r"hello&#32world", ["hello", "32world"]),
     (r"hello&#x20world", ["hello", "x20world"]),
     (r"hello&aposworld", ["hello", "aposworld"]),
     (r"hello&32;world", ["hello", "world"]),  # named entity "32"
     (r"hello&x#20;world", ["hello", "x", "20", "world"]),
     (r"hello&potatocakes;world", ["hello", "world"]),
     (r"hello& ;world", ["hello", "world"]),
     (r"hello& world", ["hello", "world"]),
     (r"hello & world", ["hello", "world"]),
     (r"hello &world", ["hello", "world"]),
     (r"hello world&", ["hello", "world"]),
     (r"hello&# ;world", ["hello", "world"]),
     (r"hello&# world", ["hello", "world"]),
     (r"hello &# world", ["hello", "world"]),
     (r"hello &#world", ["hello", "world"]),
     (r"hello world&#", ["hello", "world"]),
     (r"hello &#1c;world", ["hello", "1c", "world"]),
     (r"hello &#x1j;world", ["hello", "x1j", "world"]),

     # URL-encoding
     ("hello%world", ["hello", "world"]),
     ("hello%0world", ["hello", "0world"]),
     ("hello%20world", ["hello", "world"]),
     ("hello%201world", ["hello", "1world"]),
     ("hello#%20world", ["hello", "world"]),
     ("hello%%20world", ["hello", "world"]),
     ("hell%C3%B5%20world", ["hello", "world"]),
     ("hel%C5%82o%20world", ["hello", "world"]),
     ("hell%C3%B5%%20world", ["hello", "world"]),
     ("%68ello world", ["hello", "world"]),
     ("hello worl%64", ["hello", "world"]),
     ("hell%6f%20%77orld", ["hello", "world"]),
     ("%78", ["x"]),
     ("%", []),
     ("74% of 12", ["74", "of", "12"]),
     ("is 74%", ["is", "74"]),

     # Entities hidden in non-word smush
     (r"hello\'\x77orld", ["hello'world"]),
     (r"hello\"\x77orld", ["hello", "world"]),
     (r"hello\'%77orld", ["hello'world"]),
     (r"hello\"%77orld", ["hello", "world"]),
     (r"hello\'&#119;orld", ["hello'world"]),
     (r"hello\"&#119;orld", ["hello", "world"]),

     (r"hello,\'\x77orld", ["hello", "world"]),
     (r"hello,\"\x77orld", ["hello", "world"]),
     (r"hello,\'%77orld", ["hello", "world"]),
     (r"hello,\"%77orld", ["hello", "world"]),
     (r"hello,\'&#119;orld", ["hello", "world"]),
     (r"hello,\"&#119;orld", ["hello", "world"]),

     (r"hello\\\'\x77orld", ["hello'world"]),
     (r"hello\\\"\x77orld", ["hello", "world"]),
     (r"hello\\\'%77orld", ["hello'world"]),
     (r"hello\\\"%77orld", ["hello", "world"]),
     (r"hello\\\'&#119;orld", ["hello'world"]),
     (r"hello\\\"&#119;orld", ["hello", "world"]),

     ("hell&#111;&apos;world", ["hello'world"]),
     ("hell&#111;&quot;world", ["hello", "world"]),
     ("hell&#111;&apos;&#119;orld", ["hello'world"]),
     ("hell&#111;&quot;&#119;orld", ["hello", "world"]),
     (r"hell&#111;&apos;\x77orld", ["hello'world"]),
     (r"hell&#111;&quot;\x77orld", ["hello", "world"]),
     ))
def test_decoding(text, expect_tokens):
    """Ensure encodings, escapings and entities are decoded.
    """
    assert list(TextSplitter().split(text)) == expect_tokens


@pytest.mark.parametrize(
    "text,expect_tokens",
    (("0x0", ["0x", "0"]),
     ("0x1234", ["0x", "1234"]),
     ("0x71c765", ["0x", "71c765"]),
     ("0xdeadbeef",
      ["0x", "[LONG]", "hex", "digits"]),
     ("0xdeadbeefL", ["0xdeadbeefL"]),
     ("0x4AAAAAAAAjq6WYeRDKmebM",
      ["0x4AAAAAAAAjq6WYeRDKmebM"]),
     ("0XPmYE28fJingEYE1hThk7F4SZFf1EVe2PxVNsmv",
      ["[BASE64]"]),
     ("0XBEA020C3BD417F30DE4D6BD05B0ED310AC586CC0",
      ["0X", "[LONG]", "hex", "digits"]),
     ))
def test_prefixed_hex(text, expect_tokens):
    """Ensure prefixed hex constants are recognized and split.
    """
    assert list(TextSplitter().split(text)) == expect_tokens


def test_sub_js_escape_crasher():
    """Ensure `_sub_js_escape()` doesn't crash when fed `["\\", ""]`

    `_sub_js_escape()` used to raise an `IndexError` if fed `["\\", ""]`.
    That's now been fixed, but the error that caused it to be fed that
    sequence has also been fixed, meaning the code this testcase flexes
    wasn't being tested by any of the regular `TextSplitter().split()`
    tests, hence this testcase to flex it specifically.
    """
    splits = ["\\", ""]
    assert TextSplitter()._sub_js_escape(splits, 0) == 1
    assert splits == [SPLIT, ""]


@pytest.mark.parametrize(
    "text,expect_tokens",
    (("That\u2019s all we know.",
      ["That's", "all", "we", "know"]),
     ("Page=Login&Action=Login\';\n\t\t\treturn",
      ["Page", "Login", "Action", "Login", "return"]),
     ("/_next/static/css/99762953f4d03581.css",
      ["next", "static", "css", "[LONG]", "hex", "digits", "css"]),
     ("https://www.gstatic.com/recaptcha/releases/"
      "V6_85qpc2Xf2sbe3xTnRte7m/recaptcha__en.js",
      ["https", "www", "gstatic", "com", "recaptcha", "releases",
       "V6", "85qpc2Xf2sbe3xTnRte7m", "recaptcha", "en", "js"]),
     ("https://www.cdn.privado.ai/8eb5e30dac7d493298287704a5f578c7.js",
      ["https", "www", "cdn", "privado", "ai", "[LONG]", "hex", "digits",
       "js"]),
     ("autocompleteType autocompleteWordsAndPhrases",
      ["autocompleteType", "autocompleteWordsAndPhrases"]),
     ("63&i;return l.buffer},publicKeyCredentialToJSON:function e(t)",
      ["63", "return", "l", "buffer", "publicKeyCredentialToJSON",
       "function", "e", "t"]),
     ("http://www1.com.com/?tm=1&subid4=1714127069.0292280000&KW1=News%"
      "20Media%20Monitoring%20Tools&KW2=News%20Lead%20Distribution%20Pl"
      "atform&KW3=Newsletters&searchbox=0&domainname=0&backfill=0",
      ["http", "www1", "com", "com", "tm", "1", "subid4", "[LONG]",
       "digits", "[LONG]", "digits", "KW1", "News", "Media", "Monitoring",
       "Tools", "KW2", "News", "Lead", "Distribution", "Platform", "KW3",
       "Newsletters", "searchbox", "0", "domainname", "0", "backfill",
       "0"]),
     ("src: url(//fonts.gstatic.com/s/roboto/v18/KFOmCnqEu92Fr1Mu4mxK"
      ".woff2) format('woff2');\\n  unicode-range: U+0000-00FF, ",
      ["src", "url", "fonts", "gstatic", "com", "s", "roboto", "v18",
       "[BASE64]", "woff2", "format", "woff2", "unicode",
       "range", "U", "0000", "00FF"]),
     (r"kNEu9lE8g2RGVVvZ6clo\\u003d\x22,1,0,null",
      ["[BASE64]", "1", "0", "null"]),
     ))
def test_regressions(text, expect_tokens):
    """Check that things we improve stay improved.
    """
    assert list(TextSplitter().split(text)) == expect_tokens
