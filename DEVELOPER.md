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
docker login # currently using user shadiakiki1986 which owns the organization autofitcloud on hub.docker.com

docker build -t autofitcloud/isitfit:latest .
docker push autofitcloud/isitfit:latest
```

Also build and push an image with the tag for the installed isitfit version

```
docker build -t autofitcloud/isitfit:0.19.8 .
docker push autofitcloud/isitfit:0.19.8
```

Quick tests

```
docker run -it autofitcloud/isitfit:latest isitfit version
docker run -it -v ~/.aws:/root/.aws autofitcloud/isitfit:latest aws sts get-caller-identity
docker run -it -v ~/.aws:/root/.aws autofitcloud/isitfit:latest isitfit cost analyze
docker run -it -v ~/.aws:/root/.aws autofitcloud/isitfit:latest bash # drops into terminal inside container
# isitfit version ... # (from within the container)
```

Note about AWS Cloud9 keymap binding for `Ctrl-O`:

If using git on aws cloud9, the "Ctrl-O" is used for the "gotofiles" keyboard shortcut,
whereas a `git commit amend ... ` will open nano terminal editor for the commit message.
Nano needs the `Ctrl-O` binding for saving the commit message.
The solution to this conflict is to click on the `AWS Cloud9` menu button on the top left,
then `Open your keymap` and finally add the following to the opened keymap file

```
    { "command": "gotofile", "keys": { "win": "Ctrl-p", "mac": "Cmd-p" } }
```

This moves the `Ctrl-O` binding to `Ctrl-P`



### Release engineering

- Tests should pass
- Update version in `isitfit/__init__.py`
- Publish new git tag
- Publish to pypi
- Publish to docker hub