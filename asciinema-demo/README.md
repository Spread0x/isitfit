## asciinema-demo

Demo `isitfit` in the terminal and share with asciinema


### Installation

```
pip3 install --user lolcat
apt-get install figlet screen cowsay
```

### Usage

```
pew in isitfit_live
pip3 install --upgrade isitfit

asciinema rec
pew in isitfit_live screen -c screenrc
exit
```


### Notes


Original plan for TTY screen layout via `screenrc` above

```
|-------------------|
|   isitfit 0.10    |  <<< with "figlet"
|-------------------|
|# isitfit  |       |
|           | Save! |
|           |  \    |
|           |   cow |
|           |       |
|           |       |
|-------------------|
   ^           ^
   ^         with "cowsay"
   ^
with "isitfit"
```

`lolcat` installed from https://pypi.org/project/lolcat/ instead of the original ruby repo. (ref: https://yjyao.com/2014/09/colorful-cowsay-in-your-terminal.html)


I had intended to edit the result file with editty,
but I'm not sure it works with asciinema.
It seems it was designed for `ttyrec`

```
apt-get install ttyrec
pip3 install --user editty
ttyrec
# do some stuff
exit

ls # shows ttyrecord
```
