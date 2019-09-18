#!/bin/sh

set -e
set -x

# set caching
ISITFIT_REDIS_HOST=localhost
ISITFIT_REDIS_PORT=6379
ISITFIT_REDIS_DB=0
redis-cli -n $ISITFIT_REDIS_DB flushdb #  || echo "redis db clear failed" (eg db number out of range)


# start
echo "Test 0: version"
isitfit --version

echo "Test 1: default profile (shadiakiki1986@gmail.com@amazonaws.com)"
isitfit

echo "Test 2: non-default profile (shadi@autofitcloud.com@amazonaws.com)"
AWS_PROFILE=autofitcloud AWS_DEFAULT_REGION=eu-central-1 isitfit

echo "Test 3: default profile in region with 0 ec2 instances"
AWS_DEFAULT_REGION=eu-central-1 isitfit

echo "Test 4: optimize with default profile"
isitfit --optimize

echo "Test 5: optimize in region with 0 ec2 instances"
AWS_DEFAULT_REGION=eu-central-1 isitfit --optimize

# done
# `set -x` doesn't let the script reach this point in case of any error
echo "Tests completed"
