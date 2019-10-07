# isitfit

[![PyPI version](https://badge.fury.io/py/isitfit.svg)](https://badge.fury.io/py/isitfit)

A simple command-line tool to check if an AWS EC2 account is fit or underused.


<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Installation](#installation)
- [Usage](#usage)
  - [Pre-requisites](#pre-requisites)
  - [Synopsis](#synopsis)
  - [Display version](#display-version)
  - [Cost-weighted average utilization](#cost-weighted-average-utilization)
  - [Recommended optimizations](#recommended-optimizations)
  - [Filtering on tags](#filtering-on-tags)
  - [Generating suggested tags](#generating-suggested-tags)
    - [Basic](#basic)
    - [Advanced](#advanced)
  - [Dumping tags to CSV](#dumping-tags-to-csv)
  - [Pushing tags from CSV](#pushing-tags-from-csv)
  - [Non-default awscli profile](#non-default-awscli-profile)
  - [Caching results with redis](#caching-results-with-redis)
  - [Datadog integration](#datadog-integration)
- [What does Underused mean?](#what-does-underused-mean)
- [Changelog](#changelog)
- [Roadmap](#roadmap)
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

If you have a Datadog account, check [Example 4: datadog integration](#example-4-datadog-integration)

For pushing tags, the user/role will also need to have the following existing policy:

`ResourceGroupsandTagEditorFullAccess`


### Synopsis

To get help hints in the command-line use the `--help`
```
> isitfit --help
> isitfit tags --help
> isitfit tags dump --help
```


### Display version

Check the version of `isitfit`

```
isitfit --version
```

### Cost-weighted average utilization

Calculate AWS EC2 Cost-Weighted Average Utilization

```
> isitfit

Field                            Value
-------------------------------  -----------
Analysis start date              2019-06-07
Analysis end date                2019-09-05
EC2 machines (total)             8
EC2 machines (analysed)          3
Billed cost                      165 $
Used cost                        9 $
CWAU = Used / Billed * 100       6 %

For reference:
* CWAU >= 70% is well optimized
* CWAU <= 30% is underused
```

### Recommended optimizations

Find all recommended type changes

```
> isitfit --optimize

Recommended savings: -74 $ (over next 3 months)

Details
+---------------------+-----------------+--------------------+------------------------------------+-----------+--------------------+-----------+--------------------------------------------------+
| instance_id         | instance_type   | classification_1   | classification_2                   |   cost_3m | recommended_type   |   savings | tags                                             |
|---------------------+-----------------+--------------------+------------------------------------+-----------+--------------------+-----------+--------------------------------------------------|
| i-069a7808addd143c7 | t2.medium       | Underused          | Burstable intraday, No memory data |       117 | t2.small           |       -59 | Name = ******                                    |
| i-34ca2fc2          | t2.nano         | Normal             | No memory data                     |        14 |                    |         0 | opsworks:layer:php-app = PHP App Server          |
|                     |                 |                    |                                    |           |                    |           | opsworks:stack = ******************              |
|                     |                 |                    |                                    |           |                    |           | opsworks:instance = ********************         |
|                     |                 |                    |                                    |           |                    |           | Name = *************                             |
+---------------------+-----------------+--------------------+------------------------------------+-----------+--------------------+-----------+--------------------------------------------------+
Saving final results to /tmp/isitfit-full-41o1b4o8.csv
Save complete
```

Notice that the full final results are saved to a csv file, indicated in the line under the table: `Saving final results to /tmp/isitfit-full-...csv`

Also, intermediate results of the optimization are streamed to a csv file during the optimization.
The filename is indicated in the command output, before the table, as `Results will be streamed to /tmp/isitfit-9t0x0jj7.csv`.
This is useful to start processing results while the optimization is running.

Find only the first 1 underused instances

```
> isitfit --optimize --n=1

...
Details
+---------------------+-----------------+--------------------+------------------------------------+-----------+--------------------+-----------+--------------------------------------------------+
| instance_id         | instance_type   | classification_1   | classification_2                   |   cost_3m | recommended_type   |   savings | tags                                             |
|---------------------+-----------------+--------------------+------------------------------------+-----------+--------------------+-----------+--------------------------------------------------|
| i-069a7808addd143c7 | t2.medium       | Underused          | Burstable intraday, No memory data |       117 | t2.small           |       -59 | Name = ******                                    |
+---------------------+-----------------+--------------------+------------------------------------+-----------+--------------------+-----------+--------------------------------------------------+
...
```

### Filtering on tags

Filter optimizations for a particular tag name or tag value

```
> isitfit --optimize --filter-tags=foo
```

Apply the same filtering of tag name/value to the cost-weighted average utilization

```
> isitfit --filter-tags=inexistant

Field                            Value
-------------------------------  -----------
Analysis start date              2019-06-07
Analysis end date                2019-09-05
EC2 machines (total)             8
EC2 machines (analysed)          0
Billed cost                      0 $
Used cost                        0 $
CWAU = Used / Billed * 100       0 %
```

### Generating suggested tags

#### Basic

This generates some tags that are implied from the instance name.

For example, if there are 3 instances that share the word "app" in their names, then "app" is used as a suggested tag.

This helps to squeeze some information out of the instance names to add some tags for convenient filtering.

The algorithm runs locally on your own machine.

To use it:

```
isitfit tags suggest
isitfit --debug tags suggest
```

#### Advanced

*(Work in progress. Check [here](https://trello.com/c/eKZawuvm/12-advanced-tag-suggestions) for status)*

For more advanced tag suggestions, the `--advanced` option will
send the EC2 instance names to [AutofitCloud](https://autofitcloud.com)'s servers,
run more sophisticated algorithms for generating tag suggestions,
and push back the results to your terminal.

To use it:

```
isitfit tags suggest --advanced
isitfit --debug tags suggest --advanced
```

AutofitCloud is the company behind `isitfit`.
You can find our privacy policy at https://www.autofitcloud.com/privacy


### Dumping tags to CSV

To dump the EC2 tags in tabular format into a CSV file:

```
> isitfit tags dump

Counting EC2 instances
Found a total of 8 EC2 instances
Scanning EC2 instances: 9it [00:01,  8.72it/s]                                                                                                                                                              
Converting tags list into dataframe
Dumping data into /tmp/isitfit-tags-9vgd_bzy.csv
Done
Consider `pip3 install visidata` and then `vd /tmp/isitfit-tags-9vgd_bzy.csv` for further filtering or exploration.
More details about visidata at http://visidata.org/
```

### Pushing tags from CSV

To push EC2 tags from a CSV file:

1. Attached the policy `ResourceGroupsandTagEditorFullAccess` to the user/role executing `isitfit`

2. Export a tags dump (csv file)

```
> isitfit tags dump
```

3. Edit the csv file
4. Simulate the push of the edited csv

```
> isitfit tags push path/to/csv
```

5. Perform actual push to AWS EC2

```
> isitfit tags push path/to/csv --not-dry-run
```


### Non-default awscli profile

To specify a particular profile from `~/.aws/credentials`, set the `AWS_PROFILE` and `AWS_DEFAULT_REGION` environment variables.

For example

```
AWS_PROFILE=autofitcloud AWS_DEFAULT_REGION=eu-central-1 isitfit
```

To show higher verbosity, append `--debug` to any command call

```
isitfit --debug
```


### Caching results with redis

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


### Datadog integration

Get your datadog API key and APP key from [datadog/integrations/API](https://app.datadoghq.com/account/settings#api).

Set them to the environment variables `DATADOG_API_KEY` and `DATADOG_APP_KEY` as documented [here](https://github.com/DataDog/datadogpy#environment-variables).

Then run isitfit as usual.

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


## Roadmap

Check the public trello board [here](https://trello.com/b/RVlHtytL/isitfit)


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

Run my local tests with

```
./test_integration.sh # integration
pytest isitfit/test_* # unit
```

Update README TOC with

```
npm install -g doctoc
doctoc README.md
```

Install dev requirements

```
pip3 install -r requirements_dev.txt
```



## Support

I built `isitfit` as part of the workflow behind [AutofitCloud](https://autofitcloud.com),
the early-stage startup that I'm founding, seeking to cut cloud waste on our planet  🌎.

If you like `isitfit` and would like to see it developed further,
sign up for a pilot project at https://autofitcloud.com

Over and out!

--[u/shadiakiki1986](https://www.reddit.com/user/shadiakiki1986)
