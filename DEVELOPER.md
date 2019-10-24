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

## Updating SYNOPSIS.md

```
/bin/sh synopsis_update.sh > SYNOPSIS.md
```
