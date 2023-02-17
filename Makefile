### Defensive settings for make:
#     https://tech.davis-hansson.com/p/make/
SHELL:=bash
.ONESHELL:
.SHELLFLAGS:=-xeu -o pipefail -O inherit_errexit -c
.SILENT:
.DELETE_ON_ERROR:
MAKEFLAGS+=--warn-undefined-variables
MAKEFLAGS+=--no-builtin-rules

# We like colors
# From: https://coderwall.com/p/izxssa/colored-makefile-for-golang-projects
RED=`tput setaf 1`
GREEN=`tput setaf 2`
RESET=`tput sgr0`
YELLOW=`tput setaf 3`

PLONE6=6.0-latest

BACKEND_FOLDER=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))
DOCS_DIR=${BACKEND_FOLDER}/docs

# Python checks
PYTHON?=python3

# installed?
ifeq (, $(shell which $(PYTHON) ))
  $(error "PYTHON=$(PYTHON) not found in $(PATH)")
endif

# version ok?
PYTHON_VERSION_MIN=3.11
PYTHON_VERSION_OK=$(shell $(PYTHON) -c 'import sys; print((int(sys.version_info[0]), int(sys.version_info[1])) > tuple(map(int, "$(PYTHON_VERSION_MIN)".split("."))))')
ifeq ($(PYTHON_VERSION_OK),0)
  $(error "Need python $(PYTHON_VERSION) >= $(PYTHON_VERSION_MIN)")
endif

all: build

# Add the following 'help' target to your Makefile
# And add help text after each target name starting with '\#\#'
.PHONY: help
help: ## This help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

bin/pip:
	@echo "$(GREEN)==> Setup Virtual Env$(RESET)"
	$(PYTHON) -m venv .
	bin/pip install -U "pip" "wheel" "cookiecutter" "mxdev" "tox"

.PHONY: config
config: bin/pip  ## Create instance configuration
	@echo "$(GREEN)==> Create instance configuration$(RESET)"
	bin/cookiecutter -f --no-input --config-file instance.yaml gh:plone/cookiecutter-zope-instance

.PHONY: build-dev
build-dev: config ## pip install Plone packages
	@echo "$(GREEN)==> Setup Build$(RESET)"
	bin/mxdev -c mx.ini
	bin/pip install -r requirements-mxdev.txt

.PHONY: build
build: build-dev ## pip install Plone packages

.PHONY: clean
clean: ## Remove old virtualenv and creates a new one
	@echo "$(RED)==> Cleaning environment and build$(RESET)"
	rm -rf bin lib lib64 include share etc var instance pyvenv.cfg

.PHONY: start
start: ## Start a Plone instance on localhost:8080
	PYTHONWARNINGS=ignore ./bin/runwsgi instance/etc/zope.ini

# Lint
.PHONY: lint
lint: bin/pip  ## Lint codebase
	bin/tox -e lint

# Docs
bin/sphinx-build: bin/pip
	bin/pip install -r requirements-docs.txt

.PHONY: build-docs
build-docs: bin/sphinx-build  ## Build the documentation
	./bin/sphinx-build \
		-b html $(DOCS_DIR) "$(DOCS_DIR)/_build/html"

.PHONY: livehtml
livehtml: bin/sphinx-build  ## Rebuild Sphinx documentation on changes, with live-reload in the browser
	./bin/sphinx-autobuild \
		--ignore "*.swp" \
		-b html $(DOCS_DIR) "$(DOCS_DIR)/_build/html"
