#!/bin/sh

set -e
set -x

# set caching
ISITFIT_REDIS_HOST=localhost
ISITFIT_REDIS_PORT=6379
ISITFIT_REDIS_DB=0

# get dir of test script
TEST_DIR=`dirname "$0"`

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
echo "Test 0b: version takes less than 1 sec (visual check ATM)"
time isitfit --version

echo "Test 1: default profile (shadiakiki1986@gmail.com@amazonaws.com)"
AWS_PROFILE=shadi AWS_DEFAULT_REGION=us-west-2 isitfit

echo "Test 2: non-default profile (shadi@autofitcloud.com@amazonaws.com)"
AWS_PROFILE=autofitcloud AWS_DEFAULT_REGION=eu-central-1 isitfit

echo "Test 3: default profile in region with 0 ec2 instances"
# Note, unlike isitfit tags dump which returns a non-0 code if 0 ec2 found, this one just returns 0
AWS_DEFAULT_REGION=eu-central-1 isitfit

echo "Test 4: optimize with default profile"
isitfit --optimize

echo "Test 5: optimize in region with 0 ec2 instances"
# Note, unlike isitfit tags dump which returns a non-0 code if 0 ec2 found, this one just returns 0
AWS_DEFAULT_REGION=eu-central-1 isitfit --optimize

echo "Test 6: optimize with n=1"
isitfit --optimize --n=1

echo "Test 7: {analyse,optimize} filter-tags {ffa,inexistant}"
isitfit --optimize --filter-tags=ffa
isitfit --filter-tags=ffa

isitfit --optimize --filter-tags=inexistant
isitfit --filter-tags=inexistant

echo "Test 8.1: tags dump on 0 ec2"
AWS_PROFILE=autofitcloud AWS_DEFAULT_REGION=us-east-1 isitfit tags dump || echo "expected to fail"

echo "Test 8.2: tags dump on shadi account"
AWS_PROFILE=shadi AWS_DEFAULT_REGION=us-west-2 isitfit tags dump

echo "Test 8.3: tags suggest on 0 ec2"
AWS_PROFILE=autofitcloud AWS_DEFAULT_REGION=us-east-1 isitfit tags suggest || echo "expected to fail"

echo "Test 8.4: tags suggest on shadi account"
AWS_PROFILE=shadi AWS_DEFAULT_REGION=us-west-2 isitfit tags suggest

echo "Test 8.5: tags push on autofitcloud account"
AWS_PROFILE=autofitcloud AWS_DEFAULT_REGION=eu-central-1 isitfit --debug tags push $TEST_DIR/testFixture-tagsPush-2-newTag.csv --not-dry-run
AWS_PROFILE=autofitcloud AWS_DEFAULT_REGION=eu-central-1 isitfit --debug tags push $TEST_DIR/testFixture-tagsPush-3-renameTag.csv --not-dry-run
AWS_PROFILE=autofitcloud AWS_DEFAULT_REGION=eu-central-1 isitfit --debug tags push $TEST_DIR/testFixture-tagsPush-1-noChange.csv --not-dry-run

echo "Test 9: user shadi doesnt have access to SQS of user autofitcloud (not as provider of isitfit-api)"
AWS_PROFILE=shadi aws sqs send-message --queue-url "https://sqs.us-east-1.amazonaws.com/974668457921/isitfit-cli-974668457921-AIDA6F3WEM7AXY6Y4VWDC.fifo" --message-body bla || echo "expected to fail"

# restore the original UID
if [ -f ~/.isitfit/uid.txt.bkpDuringTest ]; then
  cp ~/.isitfit/uid.txt.bkpDuringTest ~/.isitfit/uid.txt
  rm ~/.isitfit/uid.txt.bkpDuringTest
fi

# done
# `set -x` doesn't let the script reach this point in case of any error
echo "Tests completed"
