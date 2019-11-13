Folder structure like https://github.com/pandas-dev/pandas/tree/master/pandas/tests

Two kinds of tests: unit, functional (integration TODO)

To run unit tests: `pytest`

For running a specific unit test:

```
pytest isitfit/tests/cost/redshift/test_iterator.py -k 'test_iterateCore_none'
```

To run functional tests:

```
[sudo] apt-get install redis
bash isitfit/tests/cost/test_integration.sh
bash isitfit/tests/cost/redshift/test_integration.sh
bash isitfit/tests/tags/test_integration.sh
bash isitfit/tests/test_apiDeployed.sh
```

To run functional tests in docker:

```
bash isitfit/tests/run_tests_docker.sh
```

As of 2019-10-11, the docker tests breaks at the point
where the user is prompted for visidata or not.
Also, it requires copying over the `~/.aws/credentials`
from my laptop to the aws cloud9 instance where I test.
