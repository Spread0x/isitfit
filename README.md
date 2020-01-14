# isitfit

[![PyPI version](https://badge.fury.io/py/isitfit.svg)](https://badge.fury.io/py/isitfit)

A simple command-line tool to check if an AWS EC2/Redshift account is fit or underused.


## Documentation

Check https://isitfit.autofitcloud.com


## Quickstart

Install and run with python's pip

```
pip3 install isitfit
isitfit cost analyze
isitfit cost optimize
```

Install and run with docker

```
docker pull autofitcloud/isitfit:latest
docker run -it -v ~/.aws:/root/.aws autofitcloud/isitfit:latest bash # drops within the docker container's terminal
isitfit cost analyze
isitfit cost optimize
```


## Changelog

Check [CHANGELOG.md](CHANGELOG.md)


## License

Apache License 2.0. Check file [LICENSE](LICENSE)


## Developer notes

Check [DEVELOPER.md](DEVELOPER.md)


## News

To follow our announcements:

- [twitter](https://twitter.com/autofitcloud)
- [reddit](https://www.reddit.com/r/autofitcloud)
- [discord](https://discord.gg/56zmfDc)
