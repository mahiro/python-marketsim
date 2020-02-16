#!/bin/sh
# Usage:
#   ./runtests [tests.test_module_name[.TestClassName[.test_method_name]]]
set -e
cd `dirname $0`

if [[ $# -lt 1 ]]; then
  python -m unittest discover
else
  PYTHONPATH=. python -m unittest "$@"
fi
