# isitfit

[![PyPI version](https://badge.fury.io/py/isitfit.svg)](https://badge.fury.io/py/isitfit)

A simple command-line tool to check if an AWS EC2 account is fit or underused.


<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Installation](#installation)
- [Usage](#usage)
  - [Pre-requisites](#pre-requisites)
  - [Example 1: basic usage](#example-1-basic-usage)
  - [Example 2: Using a non-default awscli profile](#example-2-using-a-non-default-awscli-profile)
  - [Example 3: caching results with redis](#example-3-caching-results-with-redis)
  - [Example 4: datadog integration](#example-4-datadog-integration)
- [What does Underused mean?](#what-does-underused-mean)
- [Changelog](#changelog)
- [License](#license)
- [Dev notes](#dev-notes)
- [Support](#support)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->



## Installation

```
pip3 install isitfit
```


## Usage

### Pre-requisites

The AWS CLI should be configured with the account's access keys:

`aws configure`

The keys should belong to a user/role with the following minimal policies:

`AmazonEC2ReadOnlyAccess, CloudWatchReadOnlyAccess`


### Example 1: basic usage

Check the version of `isitfit`

```
isitfit --version
```

Calculate AWS EC2 used-to-billed cost

```
> isitfit

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
```

Find the first 3 recommended type changes

```
> isitfit --optimize --n=2

Recommended savings: -74 $ (over next 3 months)
This table has been filtered for only the 1st 2 scan results

Details
+---------------------+-----------------+--------------------+------------------------------+-----------+--------------------+-----------+
| instance_id         | instance_type   | classification_1   | classification_2             |   cost_3m | recommended_type   |   savings |
+---------------------+-----------------+--------------------+------------------------------+-----------+--------------------+-----------|
| i-069a7808addd143c7 | t2.medium       | Underused          | Burstable, hourly resolution |       118 | t2.small           |      -59  |
| i-02432bc7          | t2.micro        | Underused          |                              |        30 | t2.nano            |      -15  |
+---------------------+-----------------+--------------------+------------------------------+---------------+--------------------+-----------+
```

Find all recommended type changes

```
> isitfit --optimize
...
```


### Example 2: Using a non-default awscli profile

To specify a particular profile from `~/.aws/credentials`, set the `AWS_PROFILE` and `AWS_DEFAULT_REGION` environment variables.

For example

```
AWS_PROFILE=autofitcloud AWS_DEFAULT_REGION=eu-central-1 isitfit
```

To show higher verbosity, append `--debug` to any command call

```
isitfit --debug
```


### Example 3: caching results with redis

Caching in `isitfit` makes re-runs more efficient.

It relies on `redis` and `pyarrow`.

To use caching, install a local redis server:

```
apt-get install redis-server
```

Set up the environment variables to point to this local redis server

```
export ISITFIT_REDIS_HOST=localhost
export ISITFIT_REDIS_PORT=6379
export ISITFIT_REDIS_DB=0
```

Use isitfit as usual

```
isitfit
isitfit --optimize
```

To clear the cache

```
apt-get install redis-client
redis-cli -n 0 flushdb
```

Consider saving the environment variables in the `~/.bashrc` file.


### Example 4: datadog integration

Get your datadog API key and APP key from [datadog/integrations/API](https://app.datadoghq.com/account/settings#api).

Set them to the environment variables `DATADOG_API_KEY` and `DATADOG_APP_KEY` as documented [here](https://github.com/DataDog/datadogpy#environment-variables).

Then run isitfit as usual, eg `isitfit` or `isitfit --optimize`

For example

```
export DATADOG_API_KEY=ABC1234
export DATADOG_APP_KEY=ABC1234
isitfit
isitfit --optimize
```

Again, consider saving the environment variables in the `~/.bashrc` file.


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
