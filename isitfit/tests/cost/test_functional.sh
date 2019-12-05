#!/bin/sh

# set caching
ISITFIT_REDIS_HOST=localhost
ISITFIT_REDIS_PORT=6379
ISITFIT_REDIS_DB=0

# clear caching
rm -rf /tmp/isitfit/ec2info.cache
redis-cli -n $ISITFIT_REDIS_DB flushdb #  || echo "redis db clear failed" (eg db number out of range)
rm -f /tmp/isitfit/iterator_cache-*.pkl

# Set the UID to the one for testing (so as not to clutter matomo data)
# This risks no longer testing the automatic creation of the folders
# but that's already covered by the unit tests anyway
if [ -f ~/.isitfit/uid.txt.bkpDuringTest ]; then
  echo "It seems that a test run was aborted."
  echo "To restore the UID backup, execute:"
  echo "mv ~/.isitfit/uid.txt.bkpDuringTest ~/.isitfit/uid.txt"
  exit 1
fi

mkdir -p ~/.isitfit
if [ -f ~/.isitfit/uid.txt ]; then
  cp ~/.isitfit/uid.txt ~/.isitfit/uid.txt.bkpDuringTest
fi
echo "bb5794d7e0294962bdefb47bab7ff0e0" > ~/.isitfit/uid.txt


# start

set -e
set -x

#echo "Test 0a: version runs ok"
#isitfit --version
#
echo "Test 0b: version takes less than 1 sec (visual check ATM, 0.7s on local, 0.2s on ec2)"
time isitfit version


echo "Test 1: on profile shadiakiki1986@gmail.com@amazonaws.com (expect in AWS_DEFAULT_REGION=us-west-2)"
AWS_PROFILE=shadi_shadi isitfit cost analyze --ndays=90


echo "Test 2: on profile shadi@autofitcloud.com@amazonaws.com (expect in AWS_DEFAULT_REGION=eu-central-1)"
AWS_PROFILE=afc_shadi_useast1 isitfit cost analyze --ndays=90


echo "Test 3: default profile in region with 0 ec2 instances"
# Note, unlike isitfit tags dump which returns a non-0 code if 0 ec2 found, this one just returns 0
isitfit cost --filter-region=eu-central-1 analyze


echo "Test 4: optimize with default profile"
isitfit cost optimize --ndays=90


echo "Test 5: optimize in region with 0 ec2 instances"
# Note, unlike isitfit tags dump which returns a non-0 code if 0 ec2 found, this one just returns 0
isitfit cost --filter-region=eu-central-1 optimize --ndays=90


echo "Test 6a: optimize with n=1 on shadi@autofitcloud.com@amazonaws.com"
AWS_PROFILE=default isitfit cost optimize --ndays=90 --n=1

echo "Test 6b: optimize with n=1 on shadiakiki1986@gmail.com@amazonaws.com"
AWS_PROFILE=shadi_shadi isitfit cost optimize --ndays=90 --n=1


echo "Test 7: {analyse,optimize} filter-tags {ffa,inexistant}"
isitfit cost optimize --ndays=90 --filter-tags=ffa
isitfit cost analyze  --ndays=90 --filter-tags=ffa

isitfit cost optimize --ndays=90 --filter-tags=inexistant
isitfit cost analyze  --ndays=90 --filter-tags=inexistant


echo "Test 8: --share-email allowed max 3 times"
isitfit --share-email=abc --share-email=fdas --share-email=fsf --share-email=fdasf cost analyze --ndays=90 || echo "expected to fail"


echo "Test 9: --share-email ok"
AWS_PROFILE=shadi_shadi isitfit --share-email=shadi@autofitcloud.com cost analyze --ndays=90


# restore the original UID
if [ -f ~/.isitfit/uid.txt.bkpDuringTest ]; then
  cp ~/.isitfit/uid.txt.bkpDuringTest ~/.isitfit/uid.txt
  rm ~/.isitfit/uid.txt.bkpDuringTest
fi

# done
# `set -x` doesn't let the script reach this point in case of any error
echo "Tests completed"
