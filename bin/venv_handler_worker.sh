#! /bin/bash

# $1 virtual env base path
# $2 PYTHONPATH
# $3 Handler path
# $4 IP address of worker host
# $5 Port number of worker, for REST requests

if [ "$#" -eq 5 ]
then
    source $1/bin/activate; PYTHONPATH=$2 python $3 --rest-host $4 --rest-port $5
else
    echo "Invalid number of arguments."
    exit 1
fi