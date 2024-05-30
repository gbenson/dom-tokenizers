import pytest

from dom_tokenizers.pre_tokenizers.splitter import TextSplitter


@pytest.mark.parametrize(
    ("text,expect_tokens"),
    (("That\u2019s all we know.",
      ["That's", "all", "we", "know"]),
     ("Page=Login&Action=Login\';\n\t\t\treturn",
      ["Page", "Login", "Action", "Login", "return"]),
     ("/_next/static/css/99762953f4d03581.css",
      ["next", "static", "css", "[LONG]", "hex", "digits", "css"]),
     ("http://www1.com.com/?tm=1&subid4=1714127069.0292280000&KW1=News%"
      "20Media%20Monitoring%20Tools&KW2=News%20Lead%20Distribution%20Pl"
      "atform&KW3=Newsletters&searchbox=0&domainname=0&backfill=0",
      ["http", "www1", "com", "com", "tm", "1", "subid4", "[LONG]",
       "digits", "[LONG]", "digits", "KW1", "News", "Media", "Monitoring",
       "Tools", "KW2", "News", "Lead", "Distribution", "Platform", "KW3",
       "Newsletters", "searchbox", "0", "domainname", "0", "backfill",
       "0"]),
     ))
def test_regressions(text, expect_tokens):
    """Check that things we improve stay improved.
    """
    assert list(TextSplitter().split(text)) == expect_tokens
