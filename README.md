<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [isitfit](#isitfit)
  - [Installation](#installation)
  - [Usage](#usage)
    - [Pre-requisites](#pre-requisites)
    - [Example 1: basic usage](#example-1-basic-usage)
    - [Example 2: Advanced usage](#example-2-advanced-usage)
    - [Example 3: caching results for efficient re-runs](#example-3-caching-results-for-efficient-re-runs)
  - [What does Underused mean?](#what-does-underused-mean)
  - [Changelog](#changelog)
  - [License](#license)
  - [Dev notes](#dev-notes)
  - [Support](#support)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# isitfit

[![PyPI version](https://badge.fury.io/py/isitfit.svg)](https://badge.fury.io/py/isitfit)

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

Recommendation value: -0.034176 $/hour
i.e. if you implement these recommendations, this is savings since negative

Details
+----+---------------------+-----------------+--------------------+------------------------------+---------------+--------------------+------------------------+
|    | instance_id         | instance_type   | classification_1   | classification_2             |   cost_hourly | recommended_type   |   recommended_costdiff |
|----+---------------------+-----------------+--------------------+------------------------------+---------------+--------------------+------------------------|
|  2 | i-069a7808addd143c7 | t2.medium       | Underused          | Burstable, hourly resolution |     0.0546118 | t2.small           |            -0.0273412  |
|  1 | i-02432bc7          | t2.micro        | Underused          |                              |     0.0136706 | t2.nano            |            -0.00683529 |
+----+---------------------+-----------------+--------------------+------------------------------+---------------+--------------------+------------------------+


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

To clear the cache

```
apt-get install redis-client
redis-cli -n 0 flushdb
```


## What does Underused mean?

isitfit categorizes instances as:

- Idle: this is an EC2 server that's sitting there doing nothing over the past 90 days
- Underused: this is an EC2 server that can be downsized at least one size
- Overused: this is an EC2 server whose usage is concentrated
- Normal: EC2 servers for whom isitfit doesn't have any recommendations


A finer degree of categorization specifies:

- Burstable: this is for EC2 servers whose workload has spikes. These can benefit from burstable machine types (aws ec2's t2 family), or moved into separate lambda functions. The server itself can be downsized at least twice afterwards.


The above categories are currently rule-based, generated from the daily cpu utilization of the last 90 days (fetched from AWS Cloudwatch).

- idle: If the maximum over 90 days of daily maximum is < 3%
- underused: If it's < 30%
- underused, convertible to burstable, if:
  - it's > 70%
  - the average daily max is also > 70%
  - but the maximum of the daily average < 30%

Sizing is simply a rule that says: "If underused, recommend the next smaller instance within the same family. If overused, recommend the next larger one."

The relevant source code is [here](https://github.com/autofitcloud/isitfit/blob/master/isitfit/optimizerListener.py#L69)



## Changelog

Check `CHANGELOG.md`


## License

Apache License 2.0. Check file `LICENSE`


## Dev notes

Local editable installation

```
pip3 install -e .
```

publish to pypi

```
python3 setup.py sdist bdist_wheel
twine upload dist/*
```

Got pypi badge from
https://badge.fury.io/for/py/git-remote-aws

Run my local tests with `./test.sh`

Update README TOC with

```
npm install -g doctoc
doctoc README.md
```



## Support

I built `isitfit` as part of the workflow behind [AutofitCloud](https://autofitcloud.com), the early-stage startup that I'm founding, seeking to cut cloud waste on our planet.

If you like `isitfit` and would like to see it developed further,
please support me by signing up at https://autofitcloud.com

Over and out!

--[u/shadiakiki1986](https://www.reddit.com/user/shadiakiki1986)
