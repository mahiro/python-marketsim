#!/bin/sh
set -e
cd `dirname $0`
module=marketsim

if ! which coverage 2>&1 > /dev/null; then
  echo "Error: please install coverage first: pip install coverage"
  exit 1
fi

if [[ $# -lt 1 ]]; then
  coverage run --source $module --branch -m unittest discover
else
  PYTHONPATH=. coverage run --source $module --branch -m unittest "$@"
fi

coverage html
echo "See ./htmlcov/index.html"
