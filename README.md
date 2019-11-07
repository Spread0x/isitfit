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
  - [Dumping tags to CSV](#dumping-tags-to-csv)
  - [Pushing tags from CSV](#pushing-tags-from-csv)
  - [Generating suggested tags](#generating-suggested-tags)
    - [Basic](#basic)
    - [Advanced](#advanced)
  - [Non-default awscli profile](#non-default-awscli-profile)
  - [Assumed roles](#assumed-roles)
  - [Caching results with redis](#caching-results-with-redis)
  - [Datadog integration](#datadog-integration)
  - [Share results by email](#share-results-by-email)
- [What does Underused mean?](#what-does-underused-mean)
- [Statistics and Usage Tracking](#statistics-and-usage-tracking)
- [Changelog](#changelog)
- [License](#license)
- [Dev notes](#dev-notes)
- [Author](#author)
- [Security contact information](#security-contact-information)

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

If you have a Datadog account, check section [Datadog integration](#datadog-integration)

For pushing tags, the user/role will also need to have the following existing policy:

`ResourceGroupsandTagEditorFullAccess`

For advanced tag suggestions and other server-side services, the following existing policy is also required:

`STS_AssumeRole`


### Synopsis

Check [SYNOPSIS.md](SYNOPSIS.md)

To get help hints in the command-line use the `--help`

```
> isitfit --help
> isitfit cost --help
> isitfit cost analyze --help
```


### Display version

Check the version of `isitfit`

```
isitfit version
```

### Cost-weighted average utilization

Calculate AWS EC2 Cost-Weighted Average Utilization

```
> isitfit cost analyze

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
> isitfit cost optimize

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
> isitfit cost optimize --n=1

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
> isitfit cost optimize --filter-tags=inexistant
```

Apply the same filtering of tag name/value to the cost-weighted average utilization

```
> isitfit cost analyze --filter-tags=inexistant
```


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


### Generating suggested tags

#### Basic

This generates some tags that are implied from the instance name.

For example, if there are 3 instances that share the word "app" in their names, then "app" is used as a suggested tag.

This helps to squeeze some information out of the instance names to add some tags for convenient filtering.

The algorithm runs locally on your own machine.

To use it:

```
isitfit tags suggest
```

#### Advanced

*(Work in progress. Check [here](https://trello.com/c/eKZawuvm/12-advanced-tag-suggestions) for status)*

For more advanced tag suggestions, the `--advanced` option will
send the EC2 instance names to the `isitfit` server-side API,
run more sophisticated algorithms there for generating tag suggestions,
and push back the results to your terminal.

To use it:

```
isitfit tags suggest --advanced
```


### Non-default awscli profile

To specify a particular profile from `~/.aws/credentials`, set the `AWS_PROFILE` and `AWS_DEFAULT_REGION` environment variables.

For example

```
AWS_PROFILE=autofitcloud AWS_DEFAULT_REGION=eu-central-1 isitfit cost analyze
```

### Assumed roles

To get `isitfit` to use a specific role, just issue `aws sts assume-role ...` and continue using `isitfit` as usual.

It will pick up the environment variables set by `assume-role`: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_SESSION_TOKEN`.

Another way is to specify the role in the `~/.aws/credentials` file as follows, and then set `AWS_PROFILE` to the role's profile name (`a_role` in the example below)

```
[a_role]
role_arn = arn:aws:iam::123456789:role/foo-bar
source_profile = profile_that_can_assume_role

[profile_that_can_assume_role]
aws_access_key_id = ABCDEF
aws_secret_access_key = 123abc456
region=us-east-1
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
isitfit cost analyze
isitfit cost optimize
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
isitfit cost analyze
isitfit cost optimize
```

Consider saving the environment variables in the `~/.bashrc` file.


### Share results by email

Use the `--share-email` option to share results by email for commands that support it.

Example usage

```
isitfit --share-email=me@example.com cost analyze
isitfit --share-email=me@example.com cost optimize
isitfit --share-email=me@example.com tags dump
isitfit --share-email=me@example.com tags suggest
isitfit --share-email=me@example.com tags push
```

To send to multiple emails, repeat the `--share-email=foo` option.
The maximum allowed number of emails is 3.



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



## Statistics and Usage Tracking

`isitfit` seeks to be driven by usage and demand of our community.
We want to understand what users are doing by collecting various events and usage data,
and we will use this data to iterate and improve `isitfit` based on this gained insight.
This includes things like the installed version of `isitfit` and the commands being used.

We do not use event payloads to collect any identifying information,
and the data is used in aggregate to understand the community as a whole.

Here is an example of a collected event:

```
Date/Time:        2019-10-05 12:34
isitfit version:  0.10
Command issued:   cost analyze
Installation ID:  abcdef123456 (random per installation)
Source IP:        123.123.123.123
Source city:      Jacksonville
Source country:   USA
```

If you use the `--share-email` option,
the email address is stored by AWS SES
to remember that it has already been verified.
The email's contents are not stored.

(Originally adapted from [serverless](https://serverless.com/framework/docs/providers/aws/cli-reference/slstats/))


## Changelog

Check [CHANGELOG.md](CHANGELOG.md)


## License

Apache License 2.0. Check file `LICENSE`




## Dev notes

Check [DEVELOPER.md](DEVELOPER.md)


## Author

`isitfit` is brought to you by [AutofitCloud](https://www.autofitcloud.com),
seeking to cut cloud waste on our planet  🌎.

If you like `isitfit`, sign up for our pilot program
to bring more cost savings to your AWS EC2 budget
while improving `isitfit` through your use cases.

- The pilot program sign up form is at the bottom of the homepage https://www.autofitcloud.com.
- To get in touch, you can use the contact form at https://www.autofitcloud.com/contact
- To follow our news and version announcements, check https://reddit.com/r/autofitcloud

<!-- twitter not so active    or https://twitter.com/autofitcloud -->

--

[Shadi Akiki](https://www.reddit.com/user/shadiakiki1986)

Founder and CEO

AutofitCloud Technologies, Inc.


## Security contact information

<!-- inspired from https://github.com/pytest-dev/pytest-mock/#security-contact-information -->

To report a security vulnerability, please use the AutofitCloud [contact page](https://autofitcloud.com/contact).

We will coordinate the fix and disclosure.

