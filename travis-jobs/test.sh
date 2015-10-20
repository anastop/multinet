#!/usr/bin/env bash

python ../bin/deploy --json-config ./test-config.json

py.test

python ../cleanup --json-config ./test-config.json
