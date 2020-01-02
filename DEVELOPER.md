## Dev notes

### Testing

Check `isitfit/tests/README.md`


### Packaging to pypi

New release

```
update version in isitfit/__init__.py
update version in changelog
commit with 'version bump 0.1.0'
git tag 0.1.0
git push origin 0.1.0
git push github 0.1.0
```

publish to pypi

```
pip3 install twine
rm build/* -rf
rm dist/* -rf
python3 setup.py sdist bdist_wheel
twine upload dist/*
```

Got pypi badge from
https://badge.fury.io/for/py/git-remote-aws


### Developing

Local editable installation

```
pip3 install -e .
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

To avoid cluttering the matomo stats,
short-circuit the URL in `/etc/hosts`
by adding the line

```
1.2.3.4   isitfit.matomo.cloud
```

### Updating SYNOPSIS.md

```
/bin/sh synopsis_update.sh > SYNOPSIS.md
```


### Asciinema demo

The https://isitfit.autofitcloud.com site hosts a demo recorded via asciinema.

Check [asciinema-demo/README.md](asciinema-demo/README.md) for more details


### Experimenting

Through jupyter notebooks

```
jupyter notebook
```

Notebooks not stored in this repository for space efficiency purposes.


### Useful redis commands

A few useful redis commands:

- To clear the cache: `redis-cli -n 0 flushdb`
- To list all keys: `redis-cli --scan --pattern '*'` ([ref](https://www.shellhacks.com/redis-get-all-keys-redis-cli/))
- To delete a particular key: `redis-cli --scan --pattern "cloudtrail_ec2type._fetch" | xargs redis-cli del` ([ref](https://rdbtools.com/blog/redis-delete-keys-matching-pattern-using-scan/))


### Building the docker image

```
docker build -t autofitcloud/isitfit:latest .
docker login # currently using user shadiakiki1986 which owns the organization autofitcloud on hub.docker.com
docker push autofitcloud/isitfit:latest
docker run -it autofitcloud/isitfit:latest isitfit version
```
