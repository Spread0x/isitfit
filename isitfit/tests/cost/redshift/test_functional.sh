#!/bin/bash

set -e
set -x

CLUSTER_ID=test-1

# create a cluster
aws redshift create-cluster \
  --cluster-identifier=$CLUSTER_ID \
  --node-type=dc2.large \
  --master-username=redshiftuser \
  --master-user-password="Abcdef123###" \
  --number-of-nodes=2 \
  --no-publicly-accessible \
  --automated-snapshot-retention-period=0 \
  --tags "Key=app,Value=isitfit-cli"


# sleep for 5 minutes, for the cluster to get created
sleep 300

# check status is "available"
aws redshift describe-clusters \
  --cluster-identifier=$CLUSTER_ID | \
  jq ".Clusters[0].ClusterStatus"

# sleep for 5 minutes again, this time for performance metrics to start showing up in cloudwatch
sleep 300

# run isitfit
isitfit cost analyze
isitfit cost optimize

# delete cluster
aws redshift delete-cluster \
  --cluster-identifier=$CLUSTER_ID \
  --skip-final-cluster-snapshot
