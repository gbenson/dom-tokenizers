<p style="float: right">
    <a href="https://badge.fury.io/py/dom-tokenizers">
         <img alt="Build" src="https://badge.fury.io/py/dom-tokenizers.svg">
    </a>
    <a href="https://github.com/gbenson/dom-tokenizers/blob/main/LICENSE">
        <img alt="GitHub" src="https://img.shields.io/github/license/gbenson/dom-tokenizers.svg?color=blue">
    </a>
</p>

# DOM tokenizers

DOM-aware tokenization for Hugging Face language models.

## TL;DR

Input:

```html
<html>
  <head>
    <meta http-equiv="content-type" content="text/html; charset=utf-8">
    <meta name="viewport" content="width=device-width">
    <title>Hello world</title>
    <script>
    document.getElementById("demo").innerHTML = "Hello JavaScript!";
    </script>
    ...
```

Output:

![<](https://gbenson.github.io/dt/ccbfee/3C.svg)![html](https://gbenson.github.io/dt/beedc6/html.svg)![>](https://gbenson.github.io/dt/f6d9ab/3E.svg)![<](https://gbenson.github.io/dt/f4aeb1/3C.svg)![head](https://gbenson.github.io/dt/a4dcf3/head.svg)![>](https://gbenson.github.io/dt/ccbfee/3E.svg)![<](https://gbenson.github.io/dt/beedc6/3C.svg)![meta](https://gbenson.github.io/dt/f6d9ab/meta.svg)![_](https://gbenson.github.io/dt/f4aeb1/5F.svg)![http](https://gbenson.github.io/dt/a4dcf3/http.svg)![equiv](https://gbenson.github.io/dt/ccbfee/equiv.svg)![=](https://gbenson.github.io/dt/beedc6/3D.svg)![content](https://gbenson.github.io/dt/f6d9ab/content.svg)![type](https://gbenson.github.io/dt/f4aeb1/type.svg)![_](https://gbenson.github.io/dt/a4dcf3/5F.svg)![content](https://gbenson.github.io/dt/ccbfee/content.svg)![=](https://gbenson.github.io/dt/beedc6/3D.svg)![text](https://gbenson.github.io/dt/f6d9ab/text.svg)![html](https://gbenson.github.io/dt/f4aeb1/html.svg)![charset](https://gbenson.github.io/dt/a4dcf3/charset.svg)![UTF](https://gbenson.github.io/dt/ccbfee/UTF.svg)![8](https://gbenson.github.io/dt/beedc6/8.svg)![>](https://gbenson.github.io/dt/f6d9ab/3E.svg)![<](https://gbenson.github.io/dt/f4aeb1/3C.svg)![meta](https://gbenson.github.io/dt/a4dcf3/meta.svg)![_](https://gbenson.github.io/dt/ccbfee/5F.svg)![name](https://gbenson.github.io/dt/beedc6/name.svg)![=](https://gbenson.github.io/dt/f6d9ab/3D.svg)![viewport](https://gbenson.github.io/dt/f4aeb1/viewport.svg)![_](https://gbenson.github.io/dt/a4dcf3/5F.svg)![content](https://gbenson.github.io/dt/ccbfee/content.svg)![=](https://gbenson.github.io/dt/beedc6/3D.svg)![width](https://gbenson.github.io/dt/f6d9ab/width.svg)![device](https://gbenson.github.io/dt/f4aeb1/device.svg)![width](https://gbenson.github.io/dt/a4dcf3/width.svg)![>](https://gbenson.github.io/dt/ccbfee/3E.svg)![<](https://gbenson.github.io/dt/beedc6/3C.svg)![title](https://gbenson.github.io/dt/f6d9ab/title.svg)![>](https://gbenson.github.io/dt/f4aeb1/3E.svg)![hello](https://gbenson.github.io/dt/a4dcf3/hello.svg)![world](https://gbenson.github.io/dt/ccbfee/world.svg)![</](https://gbenson.github.io/dt/beedc6/3C2F.svg)![title](https://gbenson.github.io/dt/f6d9ab/title.svg)![>](https://gbenson.github.io/dt/f4aeb1/3E.svg)![<](https://gbenson.github.io/dt/a4dcf3/3C.svg)![script](https://gbenson.github.io/dt/ccbfee/script.svg)![>](https://gbenson.github.io/dt/beedc6/3E.svg)![document](https://gbenson.github.io/dt/f6d9ab/document.svg)![getElementById](https://gbenson.github.io/dt/f4aeb1/getElementById.svg)![demo](https://gbenson.github.io/dt/a4dcf3/demo.svg)![innerHTML](https://gbenson.github.io/dt/ccbfee/innerHTML.svg)![Hello](https://gbenson.github.io/dt/beedc6/Hello.svg)![JavaScript](https://gbenson.github.io/dt/f6d9ab/JavaScript.svg)![</](https://gbenson.github.io/dt/f4aeb1/3C2F.svg)![script](https://gbenson.github.io/dt/a4dcf3/script.svg)![>](https://gbenson.github.io/dt/ccbfee/3E.svg)![...](https://gbenson.github.io/dt/ffffff/dotdotdot.svg)

## Why?

Natural language tokeniz(er,ation scheme)s are designed so
as to
a) group particles of meaning together
b) (omit/discard/hide) unimportant details
such that models consuming sequences of token IDs
are presented with what they need in a way they can most
easily (process/derive meaning from)
[in theory, models could consume streams of utf-8, but
the model will have to learn everything the tokenizer does
so consuming resources (layers/neurons/parameters)
and (portentally vastyl) extending training time.]

for example, tokenizers aimed at languages that delimit with
whitespace generally have features to (omit/discard/embed/hide)
whitespace in their output so the model/consumer does not need
to care about it.

this shiz aims to do a similar thing but for HTML:
whitespace is discarded,
tag names, attribute names and attribbte values are tokenized
along with the textual content of the document,

and special tokens are inserted to give context, so e.g.
start and end tags are wrapped in `<`, `</` and `>`,
attribute names are preceded by `_`
and attribute values preceeded by `=`.

## Limitations

tokenizers are usually able to operate in either direction:
both *encoding* natural language into sequences of token IDs
for the model's input,
and *decoding* sequences of token IDs generated by the model
into natural language text.

generation isn't a goal for me, for now at least: I'm interested
in extracting meaning,


, so this
tokenizer will discard some of its input in order to better distil
the meaning of what it's looking at.

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

### On the command line

Check everything's working using a small dataset of around 300 examples:

```sh
train-tokenizer gbenson/interesting-dom-snapshots
```

Train a tokenizer with a 10,000-token vocabulary using a dataset of
4,536 examples and upload it to the Hub:

```sh
train-tokenizer gbenson/webui-dom-snapshots -n 10000 -N 4536
huggingface-cli login
huggingface-cli upload dom-tokenizer-10k
```
