[![version badge]](https://pypi.org/project/dom-tokenizers/)
[![license badge]](https://github.com/gbenson/dom-tokenizers/blob/main/LICENSE)

[version badge]: https://img.shields.io/pypi/v/dom-tokenizers?color=limegreen
[license badge]: https://img.shields.io/github/license/gbenson/dom-tokenizers.svg?color=blue


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
