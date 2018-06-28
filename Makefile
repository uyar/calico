.PHONY: help clean clean-build clean-pyc clean-docs lint test test-all coverage docs dist release

release: RESPONSE = $(shell bash -c 'read -r -p "Do you want to upload [y/N]? " r; echo $$r')

help:
	@echo "clean - clean everything"
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "clean-docs - remove Sphinx documentation artifacts"
	@echo "lint - check style with flake8"
	@echo "test - run tests quickly with the default Python"
	@echo "test-all - run tests on every Python version with tox"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo "docs - generate Sphinx HTML documentation, including API docs"
	@echo "dist - package"
	@echo "release - package and upload a release"

clean: clean-build clean-pyc clean-docs

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

clean-docs:
	make -C docs clean

lint:
	flake8 calico

test:
	pytest

test-all:
	tox

coverage:
	pytest --cov-report term-missing --cov=calico tests

docs:
	$(MAKE) -C docs clean
	$(MAKE) -C docs html

setup.py: clean
	poetry build
	tar xzf dist/calico*.tar.gz --strip-components=1 --wildcards "calico-*/setup.py"
	black setup.py
	python setup.py check -r -s

dist: clean
	python setup.py sdist
	python setup.py bdist_wheel

release: dist
	@if [ $(RESPONSE)'' = 'y' ]; then twine upload dist/*; fi
