#!/bin/bash
# Tested running each command separately, not altogether in this bash script
# Note that "client-token" needs to be incremented for each new request

doreq() {
aws ec2 request-spot-instances \
  --block-duration-minutes=120 \
  --client-token=test-isitfit-spot-4 \
  --instance-count=1 \
  --spot-price=0.3 \
  --region=us-west-2 \
  --launch-specification file://spot_request_specification.json
}

res = doreq

# https://stedolan.github.io/jq/manual/
# https://stackoverflow.com/a/56800543/4126114
echo res|jq .SpotInstanceRequests[0].{SpotInstanceRequestId,Status}

# extra ID and follow up
req_id = `echo res|jq .SpotInstanceRequests[0].SpotInstanceRequestId`

# sleep
sleep 30

# check
aws ec2 describe-spot-instance-requests --region=us-west-2 --spot-instance-request-ids=$req_id
