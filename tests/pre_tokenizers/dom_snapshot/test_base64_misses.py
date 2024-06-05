from ...util import load_resource


def test_1655961866939(pre_tokenizer):
    snapshot = load_resource("1655961866939.json")
    tokens = pre_tokenizer.tokenize(snapshot)
    for token in tokens:
        assert "l0gh7uis0hpxahwelsqtpiqs2yzobl" not in token.lower(), token
