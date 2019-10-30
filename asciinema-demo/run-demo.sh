#!/bin/bash
# Usage
# ttyrec
# bash run-demo.sh
# exit
# Check output in ttyrecord

COWSAY_TXT=/tmp/isitfit-demo-cowsay-text.txt
export AWS_PROFILE=shadi_shadi

docw1() {
  clear
  figlet "    isitfit"
  echo ""
  echo "The fastest AWS EC2 cost optimizer"
  echo ""
  echo $2 | cowsay -n
  echo ""
  sleep $1
}

docw2() {
  echo $2 > $COWSAY_TXT
  sleep $1
}

typewriter()
{
    text="$1"
    delay=.1 # "$2"

    for i in $(seq 0 $(expr length "${text}")) ; do
        echo -n "${text:$i:1}"
        sleep ${delay}
    done
    echo ""
}

doisi() {
  clear
  typewriter "# $2"
  $2
  sleep $1
}

# breathe for inotifywait
sleep 1

# start
docw2 3 ""
docw2 6 "Welcome to my demo of isitfit. Let's check the installed version."
doisi 3 "isitfit version"
docw2 2 "LGTM"
doisi 1 "clear"

docw2 6 "The first step to cost optimization is measuring the efficiency. Let's calculate the cost-weighted average utilization and send it by email"
doisi 3 "isitfit --share-email=cow@isitfit.io cost analyze"
docw2 6 "The demonstrated account is underutilized at 6% only" 
doisi 1 "clear"

docw2 5 "Next, let's identify a few saving opportunities while filtering for a tag"
doisi 3 "isitfit cost optimize --n=3 --filter-tags=ffa"
docw2 6 "So we can save \$15 in the next 3 months by downsizing one server."

docw2 9 "And that's it for the demo! To check more options in isitfit, use \`isitfit --help\`, or go to https://isitfit.autofitcloud.com. Thank you!"
read
