

# THIS IS A MESS.  WHY YOU SO DIFFICULT PYENV?

VENV_NAME=venv_praisebot
VENV_ACTIVATE=$(dir $(shell pyenv which ${VENV_NAME}))/activate
WITH_VENV=. $(VENV_ACTIVATE);

.PHONY: venv
venv: $(VENV_ACTIVATE)


$(VENV_ACTIVATE): requirements*.txt
	test -f $@ || pyenv virtualenv --copies ${PYTHON_VERSION} $(VENV_NAME)
	touch $@

venv: $(VENV_ACTIVATE)
	pyenv activate ${VENV_NAME}


setup:
	$(WITH_VENV) pip install -r requirements.txt -r requirements-dev.txt


test:
	$(WITH_VENV) nosetests

run: venv setup
	$(WITH_VENV) python -m praisebot.bot

