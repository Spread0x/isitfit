#!/bin/bash
# References
# https://askubuntu.com/a/819290/543234
# Requires apt-get install inotify-tools

# Variables
COWSAY_TXT=/tmp/isitfit-demo-cowsay-text.txt


# init
echo "Hello" > $COWSAY_TXT

# trigger on change
# inotifywait -qm --event modify --format '%w' $COWSAY_TXT | xargs -I{} sh -c 'clear; figlet "   isitfit"; echo ""; cat {} | cowsay -n'
inotifywait -qm --event modify --format '%w' $COWSAY_TXT | xargs -I{} sh -c 'clear; figlet "   isitfit"; echo ""; cowsay < {}|lolcat -4'


