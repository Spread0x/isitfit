# isitfit [![PyPI version](https://badge.fury.io/py/isitfit.svg)](https://badge.fury.io/py/isitfit)

Command-line tool to calculate the AWS resource capacity excess.


## Installation

```
pip3 install isitfit
```


## Usage

```
# use default profile in ~/.aws/credentials
isitfit
isitfit --debug # show higher verbosity

# specify a particular profile
AWS_PROFILE=autofitcloud AWS_DEFAULT_REGION=eu-central-1 isitfit
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
