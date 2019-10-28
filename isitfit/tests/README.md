Folder structure like https://github.com/pandas-dev/pandas/tree/master/pandas/tests

Two kinds of tests: unit, functional (integration TODO)

To run unit tests: `pytest`

To run functional tests:

```
[sudo] apt-get install redis
bash isitfit/tests/cost/test_integration.sh
bash isitfit/tests/tags/test_integration.sh
```

To run functional tests in docker:

```
bash isitfit/tests/run_tests_docker.sh
```

As of 2019-10-11, the docker tests breaks at the point
where the user is prompted for visidata or not.
Also, it requires copying over the `~/.aws/credentials`
from my laptop to the aws cloud9 instance where I test.
