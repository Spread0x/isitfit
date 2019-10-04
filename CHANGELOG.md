Semantic versioning


Version latest (0.5.0?, 2019-09-24?)

- ...
- feat: major refactor of tags classes so that they inherit from each other
    - cleaner code :)
- feat: start on `isitfit tags suggest --advanced` that uploads ec2 names for further advanced processing
  - this currently successfully uploads csv to s3 and waits on sqs, but nothing is listening ATM to reply
  - now that I have 2 endpoints (`register` and `tags/suggest`), I'm trying to get the suggest endpoint to function (ie start listening)
  - fix sqs messages reading and factored out base url
- bugfix: raise error on 0 ec2 instances when `isitfit tags suggest [--advanced]`
- enh: add to readme the `isitfit tags suggest --advanced` feature, with a link to the privacy policy
- bugfix: skip messages in sqs queue that are not for tags suggest and auto-drop stale ones (eg from before the request timing)


Version 0.7.1 (2019-09-27)

- bugfix: add boto3 as dependency


Version 0.7.0 (2019-09-27)

- feat: `isitfit tags suggest` will generate some tags that are implied from the instance names


Version 0.6.2 (2019-09-26)

- bugfix: if no tags nor name, the optimize code was failing. Closes #5


Version 0.6.1 (2019-09-26)

- bugfix: had forgotten the instance ID in the tags dump (oops)
    - also the column sorting wasnt working


Version 0.6.0 (2019-09-26)

- feat: `isitfit tags dump` new command to dump csv of tags for use with visidata or spreadsheet editor


Version 0.5.5 (2019-09-26)

- enh: moving imports to shave on load time when `isitfit --version` is called (down from 5 seconds to 0.7 seconds)
- enh: testing script now removes the ec2 catalog cache so that downloading the URL is also tested


Version 0.5.4 (2019-09-25)

- bugfix: sloppy release before checking test results :/


Version 0.5.3 (2019-09-25)

- enh: separate consolidation of all results from displaying the consolidation
- feat: stream intermediate results to csv during the optimization
- feat: save optimization final output to csv


Version 0.5.2 (2019-09-25)

- enh: merge datadog dataframe into cloudwatch dataframe and start using it in the CWAU calculation
    - for workloads that require higher RAM than CPU, this increases the CWAU to account for the higher RAM
    - it still would punish the low CPU utilization, but at least it's taking both into account now


Version 0.5.1 (2019-09-25)

- enh: display an instance's tags in the optimization table
- feat: add `--filter-tags` option
- enh: display n ec2 analysed
- enh: move out the call to listeners from inside `handle_ec2_obj`
- enh: when filtering by tags, also filter the tags themselves


Version 0.5.0 (2019-09-25)

- enh: readme docs for examples was not up-to-date with monthly savings in `--optimize`. Updated.
- feat: merge datadog integration
- bugfix: moved the try/finally from the `__main__` section in `cli.py` to the `cli()` function
- enh: moved test for datadogManager to separate file
- bugfix: querying from datadog for a single host was missing the `host:` prefix
- enh: stop filtering the optimize output for only non-normal classification


Version 0.4.5 (2019-09-24)

- enh: atexit usage changed in favor of try/finally so that the footer message is not displayed on error
- enh: python packages redis and pyarrow are now direct dependencies (it's just simpler like this, I'm targeting large infra that needs it anyway)
- enh: python package awscli also added as a direct dependency to simplify matters further


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
