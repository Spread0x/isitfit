#!/bin/sh

set -e

# Update 2020-01-02 Dropped redis server from docker image
# service redis-server start
# sleep 1
# service redis-server status # returns non-0 if not running

python3 -m pew in isitfit "$@"
