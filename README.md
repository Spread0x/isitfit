# isitfit [![PyPI version](https://badge.fury.io/py/isitfit.svg)](https://badge.fury.io/py/isitfit)

Command-line tool to calculate the AWS EC2 capacity excess.


## Installation

```
pip3 install awscli isitfit
```


## Usage

Example usage

```
# configure awscli first
aws configure
# ...

# Calculate excess EC2 capacity
# using default profile in ~/.aws/credentials
isitfit
isitfit --debug # show higher verbosity

# specify a particular profile
AWS_PROFILE=autofitcloud AWS_DEFAULT_REGION=eu-central-1 isitfit
```

Example output

```
Cloudtrail page 1: 1it [00:01,  1.91s/it]
Cloudtrail page 1: 7it [00:05,  1.22it/s]
First pass, EC2 instance: 9it [00:01,  5.48it/s]
Second pass, EC2 instance: 9it [00:10,  1.31s/it]
IFI = 5.47%
(IFI >= 70% is well optimized)
(IFI <= 30% is underused)
```

IFI = Infrastructure Fitness Index

It is a percentage ratio of used capacity to total capacity


PS 1: the AWS keys should belong to a user/role with the following minimal policies:

`AmazonEC2ReadOnlyAccess, CloudWatchReadOnlyAccess`


PS 2: isitfit 0.1.2 only uses CPUUtilization



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
