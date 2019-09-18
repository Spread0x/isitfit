# isitfit [![PyPI version](https://badge.fury.io/py/isitfit.svg)](https://badge.fury.io/py/isitfit)

A simple command-line tool to check if an AWS EC2 account is fit or underused.


[![asciicast](https://asciinema.org/a/268751.svg)](https://asciinema.org/a/268751)


## Installation

```
pip3 install awscli isitfit
```


## Usage

### Pre-requisites

The AWS CLI should be configured with a user/role with the following minimal policies:

`AmazonEC2ReadOnlyAccess, CloudWatchReadOnlyAccess`


### Example 1: basic usage

Calculate AWS EC2 used-to-billed cost

```
> isitfit
Is it fit?

Fetching history...
... done

Cost-Weighted Average Utilization (CWAU) of the AWS EC2 account:

Field                            Value
-------------------------------  -----------
Analysis start date              2019-06-07
Analysis end date                2019-09-05
Number of EC2 machines           8
Billed cost                      165.42 $
Used cost                        9.16 $
CWAU = Used / Billed * 100       6 %

For reference:
* CWAU >= 70% is well optimized
* CWAU <= 30% is underused

* isitfit version 0.1 is based on CPU utilization only (and not yet on memory utilization)
```

Calculate recommended type changes

```
# isitfit --optimize
Is it fit?
Initializing
Fetching history...
...done


Optimization based on the following CPU thresholds:
{'idle': 3, 'low': 30, 'high': 70}

Recommendation value: 0.097238 $/hour
i.e. if you implement these recommendations, this is extra cost since positive


Details
           instance_id instance_type  max_cpu classification  cost_hourly recommended_type  recommended_costdiff
1           i-02432bc7      t2.micro       24      Underused     0.013671          t2.nano             -0.006835
2  i-08c802de5accc1e89     t3.medium       82       Overused     0.049320         t3.large              0.049320
3  i-069a7808addd143c7     t2.medium      100       Overused     0.054612         t2.large              0.054753

* isitfit version 0.1.7 is based on CPU utilization only (and not yet on memory utilization)
```


### Example 2: Advanced usage

```
# show higher verbosity
isitfit --debug

# specify a particular profile
AWS_PROFILE=autofitcloud AWS_DEFAULT_REGION=eu-central-1 isitfit

# show installed version
isitfit --version
pip3 freeze|grep isitfit
```

### Example 3: caching results for efficient re-runs

Caching in `isitfit` relies on `redis` and `pyarrow`.

To use caching:

```
apt-get install redis-server
pip3 install redis==3.3.8 pyarrow==0.14.1
export ISITFIT_REDIS_HOST=localhost
export ISITFIT_REDIS_PORT=6379
export ISITFIT_REDIS_DB=0
isitfit
```


## Recommendations

As of today (2019-09-16), recommendations are:

- Lambda: this is for EC2 servers whose workload has spikes that can be moved into separate lambda functions. The server itself can be downsized at least twice after moving the spike to lambda.
- Undersused: this is an EC2 server that can be downsized at least once
- Overused: this is an EC2 server whose usage is being concentrated
- Normal: EC2 servers for whom isitfit doesn't have any recommendations


## Changelog

Check `CHANGELOG.md`


## License

Apache License 2.0. Check file `LICENSE`


## Dev notes

```
pip3 install -e .

# publish to pypi
python3 setup.py sdist bdist_wheel
twine upload dist/*
```

Got pypi badge from https://badge.fury.io/for/py/git-remote-aws

Run my local tests with `./test.sh`



## Support

I built `isitfit` as part of the workflow behind [AutofitCloud](https://autofitcloud.com), the early-stage startup that I'm founding, seeking to cut cloud waste on our planet.

If you like `isitfit` and would like to see it developed further,
please support me by signing up at https://autofitcloud.com

Over and out!

--[u/shadiakiki1986](https://www.reddit.com/user/shadiakiki1986)
