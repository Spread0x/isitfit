# isitfit [![PyPI version](https://badge.fury.io/py/isitfit.svg)](https://badge.fury.io/py/isitfit)

A simple command-line tool to check if an AWS EC2 account is fit or underused.


## Installation

```
pip3 install awscli isitfit
```


## Usage

### Example 1: basic usage

```
> isitfit

Calculating the Cost-Weighted Average Utilization (CWAU) of the AWS EC2 account:
Fetching history...
Cloudtrail page 1: 1it [00:00,  5.18it/s]
Cloudtrail page 1: 1it [00:00, 22.43it/s]
First pass, EC2 instance: 4it [00:00, 72.76it/s]                                                                                                                             
Second pass, EC2 instance: 4it [00:00,  9.46it/s]                                                                                                                            
... done

Summary:

Field                            Value
-------------------------------  -----------
Analysis start date              2019-06-07
Analysis end date                2019-09-05
Number of analysed EC2 machines  3
Billed cost per hour             5.23 $/hour
Used cost per hour               0.18 $/hour
CWAU = Used / Billed * 100       3 %

For reference:
* CWAU >= 70% is well optimized
* CWAU <= 30% is underused
* isitfit version 0.1 is based on CPU utilization only (and not yet on memory utilization)
```


PS: the AWS keys should belong to a user/role with the following minimal policies:

`AmazonEC2ReadOnlyAccess, CloudWatchReadOnlyAccess`


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



## Support

I built `isitfit` as part of the workflow behind [AutofitCloud](https://autofitcloud.com), the early-stage startup that I'm founding, seeking to cut cloud waste on our planet.

If you like `isitfit` and would like to see it developed further,
please support me by signing up at https://autofitcloud.com

Over and out!

--[u/shadiakiki1986](https://www.reddit.com/user/shadiakiki1986)
