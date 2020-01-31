Semantic versioning


Version latest (0.18.0rc?, 2019-12-05?)

- ...


Version 0.20.9 (2020-01-31)

- bugfix: decolorize profile from terminal to include the case when putty converts the delimiter and no longer matches the regex


Version 0.20.{5..8} (2020-01-29)

- enh: improved `isitfit datadog dump y-m-d instance_id` command
- enh: stats collecting if datadog configured or not
- bugfix: check error status of datadog.`map_aws_datadog` before proceeding and getting missing key
- enh: use tags with the `www.ec2instances.info-ec2op` repo


Version 0.20.4 (2020-01-28)

- feat: for EC2 classified as `Normal`, suggest a cheaper family-generation upgrade, eg t2.nano to t3a.nano and save 20%


Version 0.20.{2,3} (2020-01-28)

- bugfix: `allow_ec2_different_family` was missing in the `isitfit cost analyze` usage of `Ec2Catalog`
- bugfix: was still referencing branch of ec2 catalog file instead of master


Version 0.20.{0,1} (2020-01-27)

- feat: add option `isitfit cost optimize --allow-ec2-different-family`
- feat: add `isitfit datadog dump i-1234` command


Version 0.19.{15..19} (2020-01-24)

- bugfix: `aws_id` is not always present in datadog hosts data


Version 0.19.{13,14} (2020-01-24)

- enh: figured out issue 10 is about datadog hostname versus AWS ID
  - added some more output to the tests in case my bugfix doesn't work
  - useful references
    - https://docs.datadoghq.com/agent/faq/how-datadog-agent-determines-the-hostname/?tab=agentv6v7#potential-host-names
    - https://docs.datadoghq.com/api/?lang=python#search-hosts
- bugfix: issue 10 uncovered that I need to map from AWS ID to Datadog hostname before I filter in datadog.. fixed
- enh: add some timer code to gather (in matomo) time-to-run of calculations
- enh: add interim timer call with number of ec2 or rds entries to calculate code performance in seconds per resource


Version 0.19.{10,11,12} (2020-01-23)

- feat: added command `isitfit issue10 host_id` for debugging issue #10


Version 0.19.9 (2020-01-09)

- bugfix: run the `aws iam get-user` only after receiving another error. Also, reword from "error" to "hint"


Version 0.19.8 (2020-01-02)

- enh: docker: dropped redis installation from docker image
- enh: move the aws credentials test at the launch of the CLI to not be run if `isitfit version` is launched
- enh: readme: add quickstart with pip and docker


Version 0.19.7 (2019-12-31)

- bugfix: add more exception handling when counting resources in regions to account for case of Roles with no access
- bugfix: added a simple `aws iam get-user` command test run at the launch of isitfit just to make sure that the user has proper credentials
    - if any error with that is faced, then probably there is a problem with the credentials in the first place


Version 0.19.6 (2019-12-27)

- feat: cost optimize: save account.cost.optimize recommendations to sqlite database, with a `dt_created` field that gets preserved between re-runs
    - this helps identify the date on which a recommendation was first created
- feat: cost optimize: do not load recommendations from sqlite instead of re-calculating
    - Update 2019-12-27
      - initially, this was "load recommendations from sqlite instead of re-calculating"
      - but I decided to just re-calculate at each request, and keep the sqlite usage to the interactive implementation
      - also, cleaned up the implementation by using the `pre` listener for checking existing sqlite (which I don't use anyway now)
    - Earlier notes 2019-12-26
      - also made some code changes for separation of concerns
      - implementation is horrible ATM, with a major requirement on how to have a different result "per ndays" request
      - the `pipeline_factory` function now got very messy as well
      - and there still is no way to pass a `--refresh` option to recalculate instead of load from sqlite
- bugfix: cost optimize: filter the `ec2_df` for only the latest size. This fixes the issue of cpu.max.max being a value for size s1 whereas the current size is s2
- bugfix: cost optimize: when `ec2_df` is shorter than 7 days of daily data, return "Not enough data" in classification



Version 0.19.5 (2019-12-23)

- enh: minor wording in "will skip" message to be more explicit


Version 0.19.4 (2019-12-23)

- enh: add `--skip-prompt-email` option
- feat: add `AccessDenied` botocore error as an exception that gets ignored (and skips region) instead of fails the run
  - this is because a user might have access to ec2 and not redshift, so still would want to get results for ec2 and not just fail halfway
  - this info gets displayed when `--debug` is issued
  - the premise is that if a user doesnt already have access to something, then s/he doesnt depend on isitfit to know that there was an error accessing a region
  - on the other hand, a user, who is getting access specifically for isitfit, would in fact want to know what s/he is missing
    - in this case, eg, the user will see "1 region" in the report and no data from any other regions, and hence will check more details
    - maybe the user would even file a github issue, to which I can highlight the use of `--debug` to check the AccessDenied errors
- enh: `base_iterator` split out `SimpleCacheMan` and made cache calls less verbose
- enh: convert the usage of `context[break_iterator]` to raising an exception `IsitfitCliRunnerBreakIterator` and then catching it in the `mainManager`
- enh: promote the stderr message "Will skip ... out of ... regions" to stdout and display it exactly once per service
- enh: split the "AWS returned AccessDenied for ... out of ... regions" into 2 parts, 1 going to stdout and the other going to stderr at `--verbose` level
- enh: if error from redis, prefix the error with "redis" to indicate it


Version 0.19.3 (2019-12-21)

- enh: use pytest parametrize for 2 tests and reduce boilerplate code
- bugfix: when exception has no .message field, CLI failed on client-side due to pinging matomo with exception. Fixed
- bugfix: `MetricCacheMixin.get_metrics_derived` was using `try/except/finally` which turns out needs the `finally` moved to after the `try/catch`
- bugfix: the redis cache (MetricCacheMixin class) was not getting used at all for both datadog and cloudwatch/ec2 due to the way I was using the inheritance .. fixed
- bugfix: the cloudwatch/redshift pipeline listener (i.e. CwRedshiftListener) was not using the redis cache at all (`MetricCacheMixin.get_metrics_derived` function) .. fixed
- bugfix: major errors in datadog api usage which were going under the radar .. fixed and added more unit tests to detect such issues
    - these are in `isitfit.cost.metrics_datadog.DatadogApiWrap`
    - also changed the 2 locations where the 1st entry of the list was taken, without checking if it indeed corresponded to the proper host


Version 0.19.2 (2019-12-19)

- feat: add sentry-sdk as a dependency along with a sentry-proxy file to send exceptions to sentry.io
  - proxy necessary to send exceptions via isitfit.io without exposing my sentry key in the isitfit-cli repository


Version 0.19.1 (2019-12-17)

- enh: add datadog missing data message to debug logs


Version 0.19.0 (2019-12-17)

- enh: rename cloudwatchman and datadogman to `metrics_cloudwatch` and `metrics_datadog`
- feat: add `metrics_auto` for automatic failover from datadog to cloudwatch
- enh: normalize dataframe column names from cloudatch and datadog
- enh: append suffix `Listener` to classes that specifically deal with the Event Bus runner, `mainManager`, and the `context_*` dictionaries
- feat: cost: major re-write of metrics fetch + misc improvements
  - cleaner fetch of metrics from datadog if enabled, with fallback to cloudwatch if missing data
  - caching no longer stores an empty dataframe when no data found, but rather a callable that raises a no-data exception if called again
  - caching TTL is 10 minutes when a callable is stored (i.e. no-data exception)
  - metrics cached split into separate mixin
  - no more `ddg_df` key in the `context_ec2` dictionary as now the `ec2_df` key comes either from datadog or from cloudwatch
  - no more `ram_used_avg.datadog` since `ram_used_avg` is a column that is available whether from datadog or cloudwatch (in the case of which it is nan)
  - normalize calls to `pandas.Dataframe.resample` in `ec2_analyze.BinCapUsed`
  - drop the `self.fix_resample_{start,end}` calls in `ec2_analyze.BinCapUsed`
  - use the event-bus listener from `metrics_auto` in `ec2_analyze` and `ec2_optimize`
  - display the status of `metrics source` as needed for debugging metric data that is available in datadog but not coming from datadog
  - split out `EventBus` from `MainManager` and inherit
  - `mainManager.ec2_noCloudwatch` no longer used in favor of `metrics_auto.sources`
  - move `NoCloudwatchException` from `utils` into `metrics_cloudwatch`
  - split out `CloudwatchAssistant` from `CloudwatchBase` and use clear function names
  - `CloudwatchCached` and `DatadogCached` use the same `MetricCacheMixin`
  - `CwRedshiftListener` now handles exception of NoCloudwatchException since no longer handled by mainManager
  - dataframe fields are `cpu_used_max` instead of `Maximum`, etc
  - when displaying migrations if `--debug` is requested, show the descriptions to dismiss doubt about migration contents
  - misc tests to accompany the code changes
- bugfix: redshift metrics are sampled every 30 seconds, not every 1 minute like ec2 .. updated formula
- enh: misc tests ironed after major updates above + still have lots of broken tests ATM
- enh: replace `sys.exit` with `raise IsitfitCliError` in `cloudtrail_iterator` (very old code)
- bugfix: datasource status for ec2 could be empty .. shouldnt fail
- enh: `csv_fn_final` for `reporter` of ec2 and redshift is deprecated in favor of the `account-level` file
  - commenting out misc deprecated code too


Version 0.18.11 (2019-12-13)

- tests: exhaustive unit tests for `datadogManager`
- bugfix: cost: datadog data was not being pulled at all when cloudwatch data was missing
    - moved the try/except of "missing cloudwatch data" to inside the per-resource iterator on listeners
    - on missing cloudwatch data, insert a single row of nans to preserve the entry for the hope that the nans will be overwritten by datadog
    - datadog cpu data overwrites the cloudwatch cpu data if present, this means that the analysis is either all-cloudwatch or all-datadog
    - add to datadog the following metrics cpu-min, ram-min, and nhours
    - conversion of datadog entries to classification was completely bugged due to the `.datadog` suffix that was added to the columns


Version 0.18.{9,10} (2019-12-13)

- bugfix: tqdm in register that waited 30 seconds to completion: didnt have `desc` field + was using tqdm directly instead of TqdmL2Verbose
- bugfix: `share/email` to not require AWS authentication, just the randomly generated local UID
  - a user didnt have `execute-api:Invoke` permission
  - another user was using the root account, which couldnt assume the isitfit-provided role
  - so just alleviating the need for any authentication altogether at this stage


Version 0.18.8 (2019-12-12)

- bugfix: strip color from profile name for case of using the default (which is colored)


Version 0.18.7 (2019-12-12)

- bugfix: in `pingOnError` check if click context ctx.obj is still None before using it
- enh: cost optimize: show message "no optimizations from ec2" in display
- feat: cost analyze: upon email entry, if sending fails because of pending verification, just prompt the user (max 3 times) to check email then click Enter when clicked on verification
- bugfix: in `IsitfitCliError`, check if `ctx` is None as well as `ctx.obj`
- bugfix: in `pingOnError` was missing a `import ping_matomo`. Not sure how it didnt show up until now
- feat: cost analyze: save the last-used email and show it as default in the email prompter
- bugfix: click issue with `--help` triggering the code of `isitfit command` when `isitfit command subcommand --help` is issued (whereas it should be skipped)
- enh: cost: use `isitfit_option_base` for `ndays` and move it back to `isitfit cost` level rather than duplicating it in `isitfit cost {analyze,optimize}`
- bugfix: cost: when `--ndays` passed on CLI, the option `type` was not being cast in `isitfit_option_base`
- enh: general: prompt for using redis now uses click.confirm and makes the default "yes" instead of "no"
- enh: cost analyze: after sending a verification email, use click.pause instead of click.prompt
- enh: cost analyze: only save "last-used email" after the email verification is complete
- feat: cost: save last-used profile in `~/.isitfit/last_profile.txt`
- feat: add colors to profile names in prompt


Version 0.18.6 (2019-12-11)

- bugfix: withdrew 0.18.5 from pypi after finding that `isitfit version` will prompt for the `--profile`
    - fixed with `cli.click_descendents.isitfit_option_profile`


Version 0.18.5 (2019-12-11)

- enh: cost analyze: use `click.IntRange` for `--ndays`
- feat: prompt user for aws profile to use
- feat: cost analyze: send profile and `filter-region` to `share-email` endpoint for display in email
- enh: refactor to move `IsitfitCliError` from `isitfit.utils` to `isitfit.cli.click_descendents`
- enh: cost analyze: add some spaces to align progress bars
- enh: cost: change default of `ndays` from 90 to 7 to inspire user repeat usage
- bugfix: cost analyze: binned start/end dates had a few small bugs: start date was not the start of the period, issues with pandas implementation of resample for 1D (end) and 1SM (semi-month), no longer filling NaT for columns with no data
- bugfix: pinging matomo before an unhandled error was causing the ping to be done 3 times, first for the command (eg isitfit cost analyze), then for the group (eg isitfit cost), and finally for the core (ie isitfit)


Version 0.18.{1,2,3,4} (2019-12-{09,10})

- bugfix: cost analyze: use resample instead of manually constructing the binned dataframe with `date_range`
  - found this issue when testing `isitfit cost analyze --ndays=15`
- bugfix: cost analyze: when no ec2/redshift data found, just raise an exception in the binning aggregator and abort early
- bugfix: cost optimize: skip the step of binning for redshift cost optimize in the "common" pipeline factory
- enh: cost analyze: pretty-print dollars/percentages in binned report
- feat: cost: increase `config.retries.max_attempts` from 4 to 10 (knowing that botocore has exponential backoff) to get around rate limiting
- enh: cost: disable the global service-level progressbar in favor of showing the individual step bars, at least until a more meaningful service-level progressbar is implemented


Version 0.18.0 (2019-12-09)

- feat: ec2 cost analyze now gathers a per-month version of the same displayed single-column table
    - still doesn't show up by default in the end result unless `--verbose` is turned on. WIP
    - add `regions_set` and `regions_str` as well as service column
    - add date start/end
    - apply the same binning class to redshift data
    - implement new display/email functions for the binned data
- bugfix: `--ndays` was not really having any effect.. fixed
- enh: include ndays in redis cache keys
- enh: `dt_end` in binned report's last column should be incremented by 1 day when ndays<64 (boto3/cloudwatch bug?)
- bugfix: redshift cost analyze to also take into account `ndays`
- bugfix: more empty-data checks
- feat, cost analyze: change binning frequency depending on the ndays option


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
