Folder structure like https://github.com/pandas-dev/pandas/tree/master/pandas/tests

Two kinds of tests: integration, unit

To run integration tests: `bash test_integration.sh`

To run unit tests: `pytest`

To run integration tests in docker: `bash isitfit/tests/run_tests_docker.sh`

As of 2019-10-11, the docker tests breaks at the point
where the user is prompted for visidata or not.
Also, it requires copying over the ~/.aws/credentials
from my laptop to the aws cloud9 instance where I test.
