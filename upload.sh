#!/bin/sh
python -m twine upload dist/* "$@"
# test: --repository-url https://test.pypi.org/legacy/
