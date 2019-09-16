#!/bin/sh

set -e
set -x

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
