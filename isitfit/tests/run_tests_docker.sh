#!/bin/sh
# Script to run docker images and execute some tests
# Copied from ec2op-cli/test/run_test_docker.sh
#------------------------------------------------------

# abort on any error
set -e

# build image
docker build ../.. -t isitfit

###############################
# live tests

# Note that even if isitfit exits with non-0 return code, the docker run still exits with 0 return code
# That's why the "echo 'test complete'" is *inside* the "docker run ... sh -c ..."
# https://docs.docker.com/develop/develop-images/build_enhancements/#using-ssh-to-access-private-data-in-builds
docker run --name isitfit_test \
           --rm \
           -v /home/ubuntu/.aws:/root/.aws \
           isitfit \
           sh /code/isitfit/tests/test_integration.sh

###############################
## mocked test
## launch 1st docker container of ec2op with the moto server
#docker run -d --name ec2optest_motoserver \
#           --rm \
#           ec2op \
#           moto_server ec2 -p3000
#
## example cycle: init, pull, optimize, add, commit
#docker run --name ec2optest_test1 \
#           --rm \
#           ec2op \
#           sh -c "ec2op init --endpoint-url='http://motoserver:3000' && ec2op pull && ec2op optimize && ec2op add us-west-2 i-1234567 && ec2op commit --message 'first commit in test'"
