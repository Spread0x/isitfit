
# Usage

How to use isitfit, in detail

---

## Pre-requisites

The AWS CLI should be configured with the account's access keys:

`aws configure`

The keys should belong to a user/role with the following minimal policies:

`AmazonEC2ReadOnlyAccess, CloudWatchReadOnlyAccess`

For Redshift analysis, the user/role also needs: `redshift:DescribeClusters`

If you have a Datadog account, check section [Datadog integration](#datadog-integration)

For pushing tags, the user/role will also need to have the following existing policy:

`ResourceGroupsandTagEditorFullAccess`

For advanced tag suggestions and other server-side services, the following existing policy is also required:

`STS_AssumeRole`


## Displaying help menus

To get help hints in the command-line use the `--help` option as follows

```
> isitfit --help
> isitfit cost --help
> isitfit cost analyze --help
```

For a full list of commands and options, check [synopsis.md](synopsis.md).


## Display version

Check the version of `isitfit`

```
isitfit version
```

## Cost-weighted average utilization

```
> isitfit cost analyze

Field                            Value
-------------------------------  -----------
Analysis start date              2019-06-07
Analysis end date                2019-09-05
EC2 Regions                      2 (us-east-1, us-west-2)
EC2 machines (total)             8
EC2 machines (analysed)          3
EC2 Billed cost                  165 $
EC2 Used cost                    9 $
EC2 CWAU = Used / Billed         6 %
Redshift Regions                 1
Redshift clusters (total)        2
Redshift clusters (analysed)     2
Redshift Billed cost             100 $
Redshift Used cost               34 $
Redshift CWAU                    34 %

For reference:
* CWAU >= 70% is well optimized
* CWAU <= 30% is underused
```

Save intermediate results to CSV files with:

```
> isitfit cost analyze --save-details

(output truncated)

Detail file 1/2: Per ec2 and day: /tmp/isitfit-cost-analyze-ec2-details-1-xd_gg2we.csv
Detail file 2/2: Per ec2 only   : /tmp/isitfit-cost-analyze-ec2-details-2-138d1ip7.csv

(output truncated)

> head -n 1 /tmp/isitfit-cost-analyze-ec2-details-1-xd_gg2we.csv
region     instance_id  Timestamp   SampleCount  Average  Minimum  Maximum  Unit    instanceType  API Name  cost_hourly  nhours
us-west-2  i-02432bc7   2019-08-29  1440.0       0.4859   0.3278   21.9999  Percent t2.micro      t2.micro  0.0136705882  24.0


> head -n 1 /tmp/isitfit-cost-analyze-ec2-details-2-138d1ip7.csv
instance_id  capacity     used
i-024...        29.54     0.14
```

Note that `isitfit cost analyze` will prompt the user for the number of days on which to perform the analysis.
By default, it's 7 days. To skip the prompt, just use the `--ndays` option, eg `isitfit cost --ndays=7 analyze`.


## Recommended optimizations

Find all recommended type changes

```
> isitfit cost optimize

Recommended savings: -74 $ (over next 3 months)

EC2 Details
+-----------+---------------------+-----------------+--------------------+------------------------------------+-----------+--------------------+-----------+--------------------------------------------------+
| region    | instance_id         | instance_type   | classification_1   | classification_2                   |   cost_3m | recommended_type   |   savings | tags                                             |
|-----------|---------------------+-----------------+--------------------+------------------------------------+-----------+--------------------+-----------+--------------------------------------------------|
| us-west-2 | i-069a7808addd143c7 | t2.medium       | Underused          | Burstable intraday, No memory data |       117 | t2.small           |       -59 | Name = ******                                    |
| us-west-2 | i-34ca2fc2          | t2.nano         | Normal             | No memory data                     |        14 |                    |         0 | opsworks:layer:php-app = PHP App Server          |
|           |                     |                 |                    |                                    |           |                    |           | opsworks:stack = ******************              |
|           |                     |                 |                    |                                    |           |                    |           | opsworks:instance = ********************         |
|           |                     |                 |                    |                                    |           |                    |           | Name = *************                             |
+-----------+---------------------+-----------------+--------------------+------------------------------------+-----------+--------------------+-----------+--------------------------------------------------+
Saving final results to /tmp/isitfit-full-41o1b4o8.csv
Save complete


Redshift cluster classification
+-----------+---------------------+------------+-----------------+-------------+-------------+--------+------------------+
| Region    | ClusterIdentifier   | NodeType   |   NumberOfNodes |   CpuMaxMax |   CpuMinMin |   Cost | classification   |
|-----------+---------------------+------------+-----------------+-------------+-------------+--------+------------------|
| us-east-1 | redshift-cluster-1  | dc2.large  |               2 |           0 |           0 |   0.25 | Normal           |
| us-east-1 | redshift-cluster-2  | dc2.large  |               3 |          56 |           0 |   0.25 | Normal           |
+-----------+---------------------+------------+-----------------+-------------+-------------+--------+------------------+
```

Notice that the full final results are saved to a csv file, indicated in the line under the table: `Saving final results to /tmp/isitfit-full-...csv`

Also, intermediate results of the optimization are streamed to a csv file during the optimization.
The filename is indicated in the command output, before the table, as `Results will be streamed to /tmp/isitfit-9t0x0jj7.csv`.
This is useful to start processing results while the optimization is running.

Find only the first `1` underused instances

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

Note that `isitfit cost optimize` will prompt the user for the number of days on which to perform the analysis.
By default, it's 7 days. To skip the prompt, just use the `--ndays` option, eg `isitfit cost --ndays=7 optimize`.


## Filtering on region

Filter all output from `isitfit cost analyze` or `isitfit cost optimize` on a certain region by using the `--filter-region` option as follows

```
isitfit cost --filter-region=us-east-1 analyze
isitfit cost --filter-region=us-east-1 optimize
```


## Filtering on tags

Filter optimizations for a particular tag name or tag value

```
> isitfit cost optimize --filter-tags=inexistant
```

Apply the same filtering of tag name/value to the cost-weighted average utilization

```
> isitfit cost analyze --filter-tags=inexistant
```


## Dumping tags to CSV

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


## Pushing tags from CSV

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


## Generating suggested tags

### Basic

This generates some tags that are implied from the instance name.

For example, if there are 3 instances that share the word "app" in their names, then "app" is used as a suggested tag.

This helps to squeeze some information out of the instance names to add some tags for convenient filtering.

The algorithm runs locally on your own machine.

To use it:

```
isitfit tags suggest
```

## Non-default awscli profile

To specify a particular profile from `~/.aws/credentials`, set the `AWS_PROFILE` environment variable.

For example

```
AWS_PROFILE=autofitcloud isitfit cost analyze
```

As of version 0.14, there is no need to set `AWS_DEFAULT_REGION`
when using `isitfit cost` because it will already scan all regions for EC2/Redshift.

You'd still need to use it for `isitfit tags` though.

To specify a single region to scan, check the section [Filtering on region](#filtering-on-region).


## Assumed roles

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

Check the [boto3 configuration](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#environment-variables) docs (sections `Environment Variables` and `Shared Credentials File`) for more details.


## Caching results with redis

Caching in `isitfit` makes re-runs more efficient.

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

Consider saving the environment variables in the `~/.bashrc` file.


## Datadog integration

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


## Share results by email

Use the `--share-email` option to share results by email.
Currently only supported by `isitfit cost analyze`

Example usage

```
isitfit --share-email=me@example.com cost analyze
```

To send to multiple emails, repeat the `--share-email=foo` option.
The maximum allowed number of emails is 3.


## Verbosity

The output from isitfit can be controlled with 2 levels of verbosity:

```
isitfit --verbose cost analyze  # show more output
isitfit --debug   cost optimize # show even more output
```

