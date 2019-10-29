#!/bin/sh
# These are tests for the CLI against the API.
# They are part of the release engineering of new API versions.
# They can also be found within isitfit/tests/{tags,cost}/test_functional.sh

set -e
set -x

deleteTestProfile() {
  aws cloudformation delete-stack --stack-name isitfit-cli-886436197218-AIDAJT35ET727AKL5Q3BS
  aws cloudformation wait stack-delete-complete --stack-name isitfit-cli-886436197218-AIDAJT35ET727AKL5Q3BS
}

# ------------------------
# cost/analyze/share-email 
# ------------------------
# call from scratch
deleteTestProfile
AWS_PROFILE=shadi_shadi isitfit --share-email=shadi@autofitcloud.com cost analyze

# call already-registered
AWS_PROFILE=shadi_shadi isitfit --share-email=shadi@autofitcloud.com cost analyze

# send to unverified email (delete identity first so that a verification email is sent)
aws ses delete-identity --identity=shadiakiki1986@gmail.com
AWS_PROFILE=shadi_shadi isitfit --share-email=shadiakiki1986@gmail.com cost analyze || echo "expected to fail + expect to receive an email"

# try again after clicking link in verification email
# TODO currently manual
# ...

# Useful command in case of need to manually re-trigger verification email
# aws ses verify-email-identity --email-address=shadiakiki1986@gmail.com

# ---------------------
# tags/suggest/advanced
# ---------------------
# call from scratch
deleteTestProfile
AWS_PROFILE=shadi_shadi isitfit tags suggest --advanced

# call already-registered
AWS_PROFILE=shadi_shadi isitfit tags suggest --advanced

##############################
# If this point is not reached, then something above must have failed
echo "Tests complete"
