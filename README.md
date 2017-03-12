# Praisebot

> Print your praises for all to see.

<img src='docs/example.png'/>

A [Slack](https://slack.com/) bot that prints labels to share thanks and celebrate wins.

## Current status

Under development.

Able to render simple handlebars templates from parsed chat messages.

Chat-bot parts are yet to be written.


## Usage

Send a Slack message of the form:
```
@praisebot <template> @<user> [with var=value+] "for"? <expression of praise>
```

* `<template>` is the name of a template, like "thank" or "highfive".
* `@user` is the @-prefixed username of the user to praise.
* 

Examples:

```
@praisebot thank @cmason for being awesome with icon=fa-star
```

```
@praisebot highfive @cmason
```

## Design/Interaction

Praisebot is started and establishes a websocket connection to Slack.

User posts slack message like the following:

```
@praisebot thank @cmason for being awesome with icon=fa-star
```

Praisebot looks up a template with the name "thank", and renders that template into an SVG.

This SVG is posted back to the channel the message was received from. Also, optionally,
a PDF file is generated and printed to a label printer.  This label can then be displayed
in meatspace for all to see!


## Installation

Detailed instructions to come.

### Mac

```
PYTHON_VERSION=3.5.3

brew install cairo pango gdk-pixbuf libxml2 libxslt libffi pyenv pyenv-virtualenv libmagic
pyenv install ${PYTHON_VERSION}
pyenv virtualenv ${PYTHON_VERSION} --copies venv_praisebot
pyenv activate venv_praisebot
pip install -r requirements.txt -r requirements-dev.txt
```

#### If python build fails with `Symbol not found: _getentropy`:

```
xcode-select --install
```

#### If you see `etree.so requires version 12.0.0 or later`:

```
brew link libxml2 --force
brew link libxslt --force
```

(from [Stackoverflow](http://stackoverflow.com/a/31607751))


#### Linux (Raspbian)

TBD


## Development

```
make setup
make test
make run  # TODO
```

## Dependencies/References

* https://www.fullstackpython.com/bots.html
* http://cairosvg.org/
* http://python-slackclient.readthedocs.io/en/latest/
* https://api.slack.com/rtm
* http://stackoverflow.com/questions/32555015/how-to-get-the-visual-length-of-a-text-string-in-python
* https://www.hmazter.com/2013/05/raspberry-pi-printer-server-for-labelwriter