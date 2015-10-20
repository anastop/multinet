#!/usr/bin/env bash

export PYTHONPATH=`pwd`

python bin/deploy --json-config config/test-config.json
echo

py.test test/
echo

python bin/cleanup --json-config config/test-config.json
echo