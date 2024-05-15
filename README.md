<p style="float: right">
    <a href="https://badge.fury.io/py/dom-tokenizers">
         <img alt="Build" src="https://badge.fury.io/py/dom-tokenizers.svg">
    </a>
    <a href="https://github.com/gbenson/dom-tokenizers/blob/master/LICENSE">
        <img alt="GitHub" src="https://img.shields.io/github/license/gbenson/dom-tokenizers.svg?color=blue">
    </a>
</p>

# DOM tokenizers

DOM-aware tokenizers for [🤗 Hugging Face](https://huggingface.co/)
language models.

## Installation

### With PIP
```sh
pip install dom-tokenizers[train]
```

### From sources

```sh
git clone https://github.com/gbenson/dom-tokenizers.git
cd dom-tokenizers
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -e .[dev,train]
```

## Train a tokenizer
```sh
train-tokenizer gbenson/interesting-dom-snapshots -n 10000
```
