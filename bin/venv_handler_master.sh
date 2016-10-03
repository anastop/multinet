#! /bin/bash

# $1 virtual env base path
# $2 PYTHONPATH
# $3 Handler path
# $4 config path

if [ "$#" -eq 4 ]
then
    source $1/bin/activate; PYTHONPATH=$2 $3 --json-config $4
else
    echo "Invalid number of arguments."
    exit 1
fi