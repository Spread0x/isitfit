# Installation

How to install python, pip, and isitfit

---

To install `isitfit` with `pip3`:

```
pip3 install isitfit
```

and then just test that it's installed with

```
isitfit version
```

## pip-fu

If you're new to python, here's some pip-fu for help.

Useful links:

- [python download instructions](https://www.python.org/downloads/)
- [pip installation instructions](http://pip.readthedocs.io/en/stable/installing/)


Install [Python](https://www.python.org/) on Ubuntu 18.04:

```
sudo apt-get install python3
```


Install [pip](http://pip.readthedocs.io/en/stable/installing/) on Ubuntu 18.04:

```
sudo apt-get install python3-pip
```

<!-- from https://www.mkdocs.org/#installation -->
Alternatively, download [get-pip.py](https://bootstrap.pypa.io/get-pip.py). Then run the following command to install it:

```
python get-pip.py
```

After having installed `pip`, there are 3 options to install `isitfit`:

- use a virtual environment (eg with [pew](https://github.com/berdario/pew)):

```
sudo pip3 install pew  # install pew globally (on all computers around the world)
pew new -d isitfit_env # create a virtual environment and don't activate it yet
pew workon isitfit_env # explicitly activate the new environment
pip3 install isitfit   # install isitfit in the activated environment only
isitfit version        # use isitfit
exit                   # de-activate the environment
```
- use sudo directly on isitfit:

```
sudo pip3 install isitfit
```

- install for the local user without a virtual environment

```
pip3 install --user isitfit
```

Note that for the `--user` option, if you've just installed `pip3`,
running `isitfit version` right after this step would yield an error `command not found`.
Restarting the machine (or log off/log on?) would set the proper environment variables so that `isitfit version` would work.


