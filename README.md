# isitfit

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

Apache


## Dev notes

```
pip3 install -e .
```
