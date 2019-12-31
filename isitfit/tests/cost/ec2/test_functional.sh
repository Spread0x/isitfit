#!/bin/bash
# Tested running each command separately, not altogether in this bash script
# Note that "client-token" needs to be incremented for each new request

AWSCLI="aws --region=us-west-2"

doreq() {
$AWSCLI ec2 request-spot-instances \
  --block-duration-minutes=120 \
  --client-token=test-isitfit-spot-4 \
  --instance-count=1 \
  --spot-price=0.3 \
  --launch-specification file://spot_request_specification.json
}

res = doreq

# https://stedolan.github.io/jq/manual/
# https://stackoverflow.com/a/56800543/4126114
echo $res|jq .SpotInstanceRequests[0].{SpotInstanceRequestId,Status}

# extra ID and follow up
req_id = `echo $res|jq .SpotInstanceRequests[0].SpotInstanceRequestId`

# sleep
sleep 30

# check
$AWSCLI ec2 describe-spot-instance-requests --spot-instance-request-ids=$req_id

# get public IP
instance_id = `echo $res|jq .SpotInstanceRequests[0].InstanceId`
res = `$AWSCLI ec2 describe-instances --instance-id=$instance_id`
echo $res | jq .Reservations[0].Instances[0].PublicIpAddress

# Install datadog agent
# https://docs.datadoghq.com/agent/basic_agent_usage/ubuntu/?tab=agentv6v7
# https://app.datadoghq.com/account/settings#agent/ubuntu (requires login)
# Check that aws security group (aws firewall) allows ssh from my source IP
# ssh -i path/to/.pem ubuntu@ip 'DD_AGENT_MAJOR_VERSION=7 DD_API_KEY=abcdef bash -c "$(curl -L https://raw.githubusercontent.com/DataDog/datadog-agent/master/cmd/agent/install_script.sh)"'
