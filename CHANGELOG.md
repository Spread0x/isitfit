Semantic versioning


Version latest (0.18.0rc?, 2019-12-05?)

- ...
- feat: ec2 cost analyze now gathers a per-month version of the same displayed single-column table
    - still doesn't show up by default in the end result unless `--verbose` is turned on. WIP
    - add `regions_set` and `regions_str` as well as service column
    - add date start/end
    - apply the same binning class to redshift data
    - implement new display/email functions for the binned data
- bugfix: `--ndays` was not really having any effect.. fixed


Version 0.17.2 (2019-12-05)

- bugfix: add init file in isitfit.migrations


Version 0.17.1 (2019-12-05)

- enh: each click group/command to have its own usage stats with its local parameters
- enh: click `cli_core:invoke_without_command=False` 
- enh: move isitfit command from utils to `cli.click_descendents`
- feat: ping matomo on uncaught click exceptions. In isitfit command and group
- bugfix: several temporary files were still getting saved into `/tmp`. Fixed
- feat: concatenate `isitfit cost optimize` tables from ec2 and redshift into one
- bugfix: better handling of case of no redshift data
- tests: functional tests for cost was still clearing the cache files from the old deprecated locations
- enh: get logger from `isitfit.utils` instead of calling logging all over the place
- bugfix: `--filter-tags` to filter the redshift clusters just like it does on ec2


Version 0.17.0 (2019-12-04)

- enh: prompt for email if user forgot to include it to share results by email
- enh: add `--verbose` flag
- enh: add a global progress bar, hide other progress bars unless `--verbose` or `--debug` requested
- enh: clean up usages of `logger.{info,warning,...}` and `click.echo`
- feat: merge displayed reports of ec2 and redshift `isitfit cost analyze` commands
- enh: move pipeline of `cost optimize` (ec2, redshift) from cli.cost to cost.service similar to pipeline of `cost analyze`
- feat: move the display step of `cost optimize` from 2 separate pipelines (ec2, redshift), to one aggregator pipeline
- enh: gather all `isitfit cost analyze` code related to `ec2` in a single file `ec2_analyze.py`
- enh: same for `optimize` and `ec2` in `ec2_optimize.py`
- bugfix: when no redshift clusters yield optimizations, had a bug in the display step
- enh: gather `ec2TagFilter` and `Ec2Common` into `ec2_common.py`
- enh: gather code for `redshift_analyze.py` and `redshift_common.py`
- enh: gather code for `redshift_optimize.py`
- enh: rename the cloudtrail iterator classes + add functional tests
- bugfix: cloudtrail data was missing the event name + had the wrong region field name
- feat: add option `isitfit cost --ndays {analyze,optimize}` for users who want to run the numbers on the most recent n days
- enh: when pinging matomo, send values of options like `ndays`
- bugfix: `save-details` option was using `logger.info` whereas it should use `click.echo`
- enh: cloudtrail empty dataframe from `all region` to not set index
- feat: add migrations module, which will take care of running maintenance tasks required between upgrades
- enh: usage stats, gather options passed to `isitfit cost`
- enh: do not check version upgrade if command is `isitfit version`
- bugfix: merged ec2-redshift pipeline to display "no optimizations from ec2" if not available
- enh: use `/tmp/isitfit/` for the iterator region cache instead of `~/.isitfit`, since it's an expirable piece of data anyway
- enh: use `/tmp/isitfit/` folder as temp dir instead of throwing everything in `/tmp` and cluttering it
- enh: use `/tmp/isitfit/` for the ec2instances.info cache
- bugfix: if pypi.python.org is unreachable, just skip it silently instead of throwing an exception
- bugfix: `isitfit cost analyze --help` was prompting for `ndays`. fixed
- enh: instead of prompting twice about sharing by email, just prompt once with blank to skip
- bugfix: upgrade `matomo_sdk_py` to set the visitor ID = user ID when tracking usage stats
- enh: ping matomo specifically on users sharing results by email


Version 0.16.{0,1} (2019-11-27)

- enh: add `--save-details` to `isitfit cost analyze` to save details behind numbers of EC2 to CSV files


Version 0.15.4 (2019-11-26)

- bugfix: `isitfit cost optimize` was not recommending anything for `idle`


Version 0.15.3 (2019-11-22)

- enh: instead of 4 progress bars per cloudtrail region, just one for all regions


Version 0.15.2 (2019-11-20)

- enh: simplify cli.cost code by gathering all the mainManager setup code into `pipeline_factory` files
- enh: refactor to rename `*Listener` to `Calculator*Ec2` and `Analyzer*` to `Calculator*Redshift`
- bugfix: when redshift total > 0 but analysed = 0, do not throw exception
- enh: when iterator total=0, do not show message saying 0 resources in 0 regions
- feat: cloudtrail extended from ec2 to redshift also. Redshift cluster history now integrated into calculation of CWAU (similar to ec2, to account for changes in type/number of nodes)


Version 0.15.1 (2019-11-20)

- bugfix: redshift cost optimize total number analyzed was always 0. Fixed to use context variable
- bugfix: `isitfit cost optimize --n=1` was not breaking early properly. fixed
- bugfix: ec2 reporters: cleaned up usage of `n_{ec2,rc}_{total,analysed}` and `region_include`; calculating `n_*_analysed` in the analyzer; dropping `n_ec2_analysed` from mainManager
- bugfix: when datadog is not configured, the `per_ec2` listener should return the context as is, not None, thus breaking the chain for the `optimizerListener`
- enh: reporters: clean up usage of `analyzer` and `mainManager` in reporters
- enh: small test improvements


Version 0.15.0 (2019-11-19)

- enh: split out iterator from fetching cloudwatch data (in redshift.iterator)
- enh: use exception instead of propagating missing cloudwatch data
- enh: move cost.mainManager parts about cloudwatch to use cost.redshift.cloudwatchman. Now redshift metrics are also cached to redis
- enh: factor out datadog cached manager to a class, planning to inherit from the same base class as CloudwatchCached
- enh: move datadog caching into class that inherits from non-cached class
- enh: split out report from ec2 analyzer
- enh: split out report from ec2 optimizer
- enh: share a context dict between `per_ec2` listeners instead of passing a list of objects
- enh: move datadog out of mainManager and into listeners
- enh: move `filter_tags` and `handle_ec2obj` out of mainManager ec2 loop and into listeners
- enh: move `cloudwatchman` out of `mainManager.handle_ec2obj` into listener
- enh: move `cloudtrail` manager out of `mainManger` to listeners
- enh: move `cache_man` to listener
- enh: move `ec2_catalog` and create `ec2_common` out of the code in `mainManager` which isn't really part of the workflow
- enh: move iterator out of mainManager to cli.cost
- bugfix: ec2.reporter objects were not compliant with the new `context_all` argument format. Fixed.
- enh: redshift reports now compatible with the `context_all` argument format
- enh: (major) redshift pipelines now use the mainmanager runner, similar to the ec2 pipeline
- feat: add `--filter-region` option to `isitfit cost`


Version 0.14.0 (2019-11-15)

- feat: ec2 cost analyze/optimize also covers all regions
- bugfix: redis caching of missing data was checking for None, but should have checked for shape==0
- enh: add dependency on `simple_cache` for caching to local file of which regions are non-empty
- bugfix: found yet another place in the code where `tags` is None hence not iterable


Version 0.13.{2,3} (2019-11-13)

- enh: split the cost.redshift.analyzer into base and derived classes for cleaner code
- enh: calculation of CWAU revised to use the average CPU, wherease the max CPU is used for the recommendations
- enh: bring back billed/used cost entries in CWAU
- enh: add integration tests to redshift cost analyze/optimize
- feat: redshift cost: cover all regions
- bugfix: redshift cost: do not multiply by 90 in analyzer since already length of dataframes = number of days
- bugfix: redshift cost: account for fractional days on first/last day


Version 0.13.{0,1} (2019-11-12)

- feat: redshift clusters cost analysis/optimization (no redis caching)
- bugfix: test for apiman was not properly mocking the requests


Version 0.12.8 (2019-11-12)

- enh: set expiry to 1 day on redis cached items if data found, otherwise 10 minutes for missing data
- bugfix: progress bar to start from 0 not from 1 to avoid issue of "101 items" at end when only "100 items" available
- enh: show number of instances for which missing cloudwatch/cloudtrail data
- enh: add link to github issues in display footer function
- enh: installation docs in readme expanded for newcomers


Version 0.12.7 (2019-11-08)

- hotfix: `isitfit cost optimize` borks when an ec2 has no tags and not even a name. Addresses #8
  - https://github.com/autofitcloud/isitfit/issues/8


Version 0.12.6 (2019-11-08)

- hotfix: ping matomo stats on exception IsitfitCliError


Version 0.12.5 (2019-10-29)

- bugfix: change handling of `registration in progress` to be not via exception
  - this is so that the `tags_suggest.advanced` can check `r_register` and see that the last code was `registration in progress` and re-trigger registration
- enh: split out `baseMan.BASE_URL` into `BASE_{HOST,PREFIX}` to allow for testing against dev API
- enh: use tabulate in showing resources to which user is granted access
- bugfix: `apiman.request` treating response is now `if/elif` instead of `if... if...`
- enh: add `test_apiDeployed.sh` to facilitate testing against API


Version 0.12.{3,4} (2019-10-28)

- enh: move apiman.register.schemaValidation to apiman.request since all responses from isitfit-api will match the general schema
- enh: add treat 'registration in progress' in the apiman.request function
- bugfix: `isitfit tags suggest --advanced` had a bug in checking that registration was ok
- enh: add `apiman.r_body` as shortcut


Version 0.12.2 (2019-10-28)

- enh: use click's exception handling for IsitfitCliError
	- pass `is_outdated` in click context for error verbosity about upgrade
- enh: use click's Command to display footer after invoke
- end: unit tests for the above changes
- enh: use click's UsageError for the deprecated options
- enh: use click's BadParameter for n of emails > 3
- enh: in `ApiMan.request`, add case of status code not "ok"


Version 0.12.{0,1} (2019-10-28)

- enh: `utils.ping_matomo` to use the new package `matomo-sdk-py`


Version 0.11.{6,7} (2019-10-25)

- enh: refactor `IsitfitError` for `IsitfitCliError`
- bugfix: change format of payload sent to cost analyze share email
  - initially the color codes were cluttering the email html
- bugfix: cost analyze share email data field 'color' should be string


Version 0.11.{2,3,4,5} (2019-10-24)

- series of fixups to publish 0.11 to pypi
- bugfix: move `isitfit --version` deprecation in favor of `isitfit version` before
- enh: wrap call to cloudtrail with try/except for cleaner exit on error
- enh: fix some tests
- bugfix: uncomment debugging of prompt upgrade
- bugfix: bring `findPackages` to `setup.py`


Version 0.11.1 (2019-10-24)

- enh: factor out code into `ApiMan` (for listening on SQS and calling AWS API Gateway endpoint) and new class EmailMan
    - this makes the code much simpler with `listen_sqs` call instead of all the internals showing up in `tagsSuggestAdvanced`
- feat: http requests to aws api gateway to be sigv4-signed with aws keys (in order to do clean authentication on http)
    - this alleviates the need to do further authentication via sqs for example (where sqs is limited to the source account by iam policy)
- bugfix: redis cache to check *all* variables set
- enh: when n ec2 > 10, prompt user to use redis caching
- bugfix: http/sqs combo request was dropping messages since `dt_now` was calculated *after* request .. fixed
- bugfix: sigv4 with aws-requests-auth updated
- bugfix: add assume role with boto3 after realizing that the aws auth doesnt work for non-autofitcloud accounts
- bugfix: path /register in `isitfit tags suggest --advanced` still requires IAM auth via sigv4
- enh: stats to be skipped on first error to reach matomo
- enh: upgrading client in response to process change about registration in `isitfit-api==0.5` since it takes > 30 seconds
- enh: implement try-again in apiman
- enh: `--share-email` is now a list by click usage
- enh: move check for deprecated usage to top of cli for faster execution
- enh: add back `--version` and list it as deprecated
- enh: add `--skip-check-upgrade` option
- enh: add `SYNOPSIS.md`
- enh: improve the `prompt_upgrade` function for the case of dev machine version being more recent than pypi
- feat: `--share-email` works with `isitfit-api==0.08`
- docs: readme links to other md files
- docs: add security section to readme
- enh: validate response schema from share-email
- enh: validate response schema envelope for all requests (i.e. 2 main keys `isitfitapi_{status,body}`)
- enh: limit share-email to 3
- enh: cli move prompt upgrade till after checking share-email limit if requested
- enh: check if share-email is to 0 emails
- enh: cli footer aligned


Version 0.11.0 (2019-10-15)

- bugfix: matomo ping was being called from test, thus cluttering the stats with noise. Mocked out
- enh: `isitfit version` and `isitfit --version` both show the version (in case a user uses any of the 2)
- enh: move all cost-related code into `isitfit/cost`
- enh: move all tags-related code into `isitfit/tags`
- enh: drop support for the optionless `isitfit` and `isitfit --optimize` in favor of `isitfit cost analyze` and `isitfit cost optimize`
  - this makes for a cleaner implementation of the CLI
  - it might confuse some early users who read earlier documentation
  - but I'd rather make this change earlier better than later
- enh: instead of showing a "option not found" error if `isitfit` or `isitfit --optimize` are used, show the user the new command syntax


Version 0.10.2 (2019-10-11)

- enh: move tests into `isitfit/tests`
- enh: add dockerfile to test in clean environment
- enh: move DotMan to separate file (out of utils) with functional tests


Version 0.10.1 (2019-10-09)

- feat: check latest version with `outdated` and ask users to upgrade
- feat: use custom domain api.isitfit.io instead of amazonaws endpoint for `isitfit tags suggest --advanced`
- feat: use matomo cloud to collect anonymous usage statistics


Version 0.9.1 (2019-10-08)

- bugfix: pyarrow upgraded to 0.15.0 after report in #6


Version 0.9.0 (2019-10-07)

- enh: replace ValueError with IsitfitError
- feat: `isitfit tags push csv_filename`


Version 0.8.4 (2019-10-04)

- hotfix: still had bug with display df hotfix
  - why do I release before testing!?!?


Version 0.8.3 (2019-10-04)

- hotfix: wrong import for `display_df`


Version 0.8.2 (2019-10-04)

- hotfix: `isitfit tags dump` was not handling ValueError
- hotfix: `MAX_ROWS` was moved to `utils` already, but had wrong import


Version 0.8.1 (2019-10-04)

- enh: use `isitfit-tags-suggestBasic-...csv` instead of `...suggest...` to highlight that an advanced suggestion is available
- feat: can open results table of `isitfit --optimize` with visidata directly


Version 0.8.0 (2019-10-04)

- feat: major refactor of tags classes so that they inherit from each other
    - cleaner code :)
- feat: start on `isitfit tags suggest --advanced` that uploads ec2 names for further advanced processing
  - this currently successfully uploads csv to s3 and waits on sqs, but nothing is listening ATM to reply
  - now that I have 2 endpoints (`register` and `tags/suggest`), I'm trying to get the suggest endpoint to function (ie start listening)
  - fix sqs messages reading and factored out base url
  - enh: bucket name in tags suggest advanced to be from register output
  - bugfix: tempfile suffix to include the "."
  - bugfix: upload of csv fixed. Was only saving filename, now saving dataframe
  - bugfix: download of result of advanced tag suggestion was not properly downloading
  - enh: more --debug output
  - enh: start using "schema" package similar to isitfit-server
  - enh: add to readme the `isitfit tags suggest --advanced` feature, with a link to the privacy policy
  - bugfix: skip messages in sqs queue that are not for tags suggest and auto-drop stale ones (eg from before the request timing)

- bugfix: raise error on 0 ec2 instances when `isitfit tags suggest [--advanced]`
- enh: stderr message showing "enabled debug level"


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
