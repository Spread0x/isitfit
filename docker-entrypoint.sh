#!/bin/sh

set -e

service redis-server start
sleep 1
service redis-server status # returns non-0 if not running

python3 -m pew in isitfit "$@"