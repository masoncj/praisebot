# Praisebot

> Print your praises for all to see.

A Slack bot that prints labels to share thanks and celebrate wins.


## Design/Interaction

Praisebot is started and establishes a websocket connection to Slack.

User posts slack message like the following:

```
@praisebot thank @cmason for being awesome with icon=fa-star
```



## Installation


### Mac

```
PYTHON_VERSION=3.5.3

brew install cairo pango gdk-pixbuf libxml2 libxslt libffi pyenv pyenv-virtualenc libmagic
pyenv install ${PYTHON_VERSION}
pyenv virtualenv ${PYTHON_VERSION} venv_praisebot
pyenv activate venv_praisebot
pip install -r requirements.txt
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
make run
```

## Dependencies/References
* https://www.fullstackpython.com/bots.html
* http://cairosvg.org/
* http://python-slackclient.readthedocs.io/en/latest/
* https://api.slack.com/rtm
* http://stackoverflow.com/questions/32555015/how-to-get-the-visual-length-of-a-text-string-in-python
* https://www.hmazter.com/2013/05/raspberry-pi-printer-server-for-labelwriter