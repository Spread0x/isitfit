#!/bin/sh

set -e
set -x

# set caching
ISITFIT_REDIS_HOST=localhost
ISITFIT_REDIS_PORT=6379
ISITFIT_REDIS_DB=0

# clear caching
rm -rf /tmp/isitfit_ec2info.cache
redis-cli -n $ISITFIT_REDIS_DB flushdb #  || echo "redis db clear failed" (eg db number out of range)

# Set the UID to the one for testing (so as not to clutter matomo data)
# This risks no longer testing the automatic creation of the folders
# but that's already covered by the unit tests anyway
if [ -f ~/.isitfit/uid.txt.bkpDuringTest ]; then
  echo "It seems that a test run was aborted."
  echo "Options:"
  echo "- Restore the UID backup: mv ~/.isitfit/uid.txt.bkpDuringTest ~/.isitfit/uid.txt"
  echo "- Remove the UID backup: rm ~/.isitfit/uid.txt.bkpDuringTest"
  exit 1
fi

mkdir -p ~/.isitfit
if [ -f ~/.isitfit/uid.txt ]; then
  cp ~/.isitfit/uid.txt ~/.isitfit/uid.txt.bkpDuringTest
fi
echo "bb5794d7e0294962bdefb47bab7ff0e0" > ~/.isitfit/uid.txt

# start
#echo "Test 0a: version runs ok"
#isitfit --version
#
echo "Test 0b: version takes less than 1 sec (visual check ATM, 0.7s on local, 0.2s on ec2)"
time isitfit version

echo "Test 1: default profile (shadiakiki1986@gmail.com@amazonaws.com)"
AWS_PROFILE=shadi AWS_DEFAULT_REGION=us-west-2 isitfit cost analyze

echo "Test 2: non-default profile (shadi@autofitcloud.com@amazonaws.com)"
AWS_PROFILE=autofitcloud AWS_DEFAULT_REGION=eu-central-1 isitfit cost analyze

echo "Test 3: default profile in region with 0 ec2 instances"
# Note, unlike isitfit tags dump which returns a non-0 code if 0 ec2 found, this one just returns 0
AWS_DEFAULT_REGION=eu-central-1 isitfit cost analyze

echo "Test 4: optimize with default profile"
isitfit cost optimize

echo "Test 5: optimize in region with 0 ec2 instances"
# Note, unlike isitfit tags dump which returns a non-0 code if 0 ec2 found, this one just returns 0
AWS_DEFAULT_REGION=eu-central-1 isitfit cost optimize

echo "Test 6: optimize with n=1"
isitfit cost optimize --n=1

echo "Test 7: {analyse,optimize} filter-tags {ffa,inexistant}"
isitfit cost optimize --filter-tags=ffa
isitfit cost analyze --filter-tags=ffa

isitfit cost optimize --filter-tags=inexistant
isitfit cost analyze --filter-tags=inexistant


# restore the original UID
if [ -f ~/.isitfit/uid.txt.bkpDuringTest ]; then
  cp ~/.isitfit/uid.txt.bkpDuringTest ~/.isitfit/uid.txt
  rm ~/.isitfit/uid.txt.bkpDuringTest
fi

# done
# `set -x` doesn't let the script reach this point in case of any error
echo "Tests completed"
