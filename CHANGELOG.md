Version latest (0.1.7?, 2019-09-??)

- ...


Version 0.4.4 (2019-09-24)

- enh: clearer stdout messages
- enh: optimization to show savings in 3 month interval (similar to analysis over 3 months)


Version 0.4.3 (2019-09-19)

- feat: add option `--n` to `--optimize` to find the first n optimizations and stop early


Version 0.4.2 (2019-09-18)

- enh: use tabulate to pretty print the pandas dataframes for the optimization


Version 0.4.1 (2019-09-18)

- bugfix: just a version bump because pypi is not providing 0.4.0 upon pip install despite showing it on https://pypi.org/project/isitfit/
  - turns out it's pypi that slow to propagate the latest version


Version 0.4.0 (2019-09-18)

- enh: replace "lambda" with "underused/burstable {hourly,daily}"
- feat: support caching through redis via environment variables


Version 0.3.2 (2019-09-16)
- enh: when no recommendations, show cleaner output


Version 0.3.1 (2019-09-16)

- enh: add documentation in readme about recommendations
- enh: stricter "overused" classifier, lambda classifier to output a 2nd classification of hourly vs daily resolution


Version 0.3.0 (2019-09-16)

- FEAT: add optimizer for recommending lambda functions (in addition to the rightsizer)


Version 0.2.5 (2019-09-13)

- bugfix: cloudtrail events to checked more thoroughly for keys (for issue #3)


Version 0.2.4 (2019-09-13)

- bugfix: tqdm dependency added


Version 0.2.3 (2019-09-13)

- bugfix: mysetlocale was still referenced from git-remote-aws


Version 0.2.2 (2019-09-13)

- enh: add link to isitfit.autofitcloud.com in cli footer


Version 0.2.1 (2019-09-13)

- enh: cleaner status bar by moving missing cloudwatch/cloudtrail data instances to after the status bar
- enh: add colors to terminal output to highlight important information


Version 0.2.0 (2019-09-13)

- enh: split out code for the listener design pattern for utilization
- feat: add basic maxmax optimizer listener


Version 0.1.6 (2019-09-05, 2019-09-13)

- enh: ec2 catalog to be downloaded with CDN rather than direct github raw link
- enh: copy `pull_cloudtrail_lookupEvents.py` from `git-remote-aws` to `isitfit` and severing the dependency


Version 0.1.5 (2019-09-10)

- bugfix: early return in case of no ec2 instances found
- enh: download ec2 catalog AFTER checking if there are any ec2 instances
- enh: display number of ec2 instances in stdout


Version 0.1.4 (2019-09-10)

- bugfix: cli output is actually `$` and not `$/hr`
- enh: add `--version` flag
- enh: clearer debug/warning logging
- bugfix: case of `sum_capacity=0` no longer throwing error (closes #1)
- bugfix: data from cloudwatch in last 90 days is 1-minute not 5-minutes



Version 0.1.3 (2019-09-05)

- ENH: use CWAU terminology instead of IFI
- ENH: show total cost per hour and used cost per hour
- ENH: add number of ec2 machines scanned
- ENH: use tabulate for the results + show start/end dates of analysis


Version 0.1.2 (2019-09-03)

- BUGFIX: remove caching of cloudtrail since it doesn't generalize well yet (between profiles)


Version 0.1.1 (2019-09-03)

- ENH: version bump for git-remote-aws 0.5.2


Version 0.1.0 (2019-09-03)

- FEAT: first release of working version
- FEAT: add setup.py and use click and now executable is just `isitfit`
- FEAT: add `--debug` flag
