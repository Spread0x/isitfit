#!/bin/sh

set -e
set -x

# default profile (shadiakiki1986@gmail.com@amazonaws.com)
isitfit

# non-default profile (shadi@autofitcloud.com@amazonaws.com)
AWS_PROFILE=autofitcloud AWS_DEFAULT_REGION=eu-central-1 isitfit

# default profile in region with 0 ec2 instances
AWS_DEFAULT_REGION=eu-central-1 isitfit

# done
# `set -x` doesn't let the script reach this point in case of any error
echo "Tests completed"
