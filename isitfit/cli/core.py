# RuntimeError: Click will abort further execution because Python 3 was configured to use ASCII as encoding for the environment.
# Consult https://click.palletsprojects.com/en/7.x/python3/ for mitigation steps.
#
# Edit 2019-10-08: whatsapp's wadebug uses "click.disable_unicode_literals_warning = True"
# Ref: https://github.com/WhatsApp/WADebug/blob/958ac37be804cc732ae514d4872b93d19d197a5c/wadebug/cli.py#L23
from ..utils import mysetlocale
mysetlocale()


from isitfit.utils import logger


import click

from .. import isitfit_version


# For the --share-email "multiple options"
# https://click.palletsprojects.com/en/7.x/options/#multiple-options
from isitfit.cli.click_descendents import isitfit_group
@isitfit_group(invoke_without_command=False)
@click.option('--debug', is_flag=True, help='Display more details to help with debugging')
@click.option('--verbose', is_flag=True, help='Display more details to help with understanding program flow')
@click.option('--optimize', is_flag=True, help='DEPRECATED: use "isitfit cost optimize" instead', hidden=True)
@click.option('--version', is_flag=True, help='DEPRECATED: use "isitfit version" instead', hidden=True)
@click.option('--share-email', multiple=True, help='Share result to email address')
@click.option('--skip-check-upgrade', is_flag=True, help='Skip step for checking for upgrade of isitfit')
@click.option('--skip-prompt-email', is_flag=True, help='Skip the prompt to share result to email address')
@click.pass_context
def cli_core(ctx, debug, verbose, optimize, version, share_email, skip_check_upgrade, skip_prompt_email):
    # FIXME click bug: `isitfit cost --help` is calling the code in here. Workaround is to check --help
    import sys
    if '--help' in sys.argv: return

    # make sure that context is a dict
    ctx.ensure_object(dict)

    # set up exception aggregation in sentry.io
    from isitfit import sentry_proxy
    from isitfit.apiMan import BASE_URL
    sp_url = f"{BASE_URL}fwd/sentry"
    sentry_proxy.init(dsn=sp_url)

    # test exception caught by sentry. FIXME Dont commit this! :D
    # 1/0

    # usage stats
    # https://docs.python.org/3.5/library/string.html#format-string-syntax
    from isitfit.utils import ping_matomo, b2l
    ping_url = "/?debug={}&verbose={}&share_email={}&skip_check_upgrade={}"
    ping_url = ping_url.format(b2l(debug), b2l(verbose), b2l(len(share_email)>0), b2l(skip_check_upgrade))
    ping_matomo(ping_url)

    # choose log level based on debug and verbose flags
    import logging
    logLevel = logging.DEBUG if debug else (logging.INFO if verbose else logging.WARNING)

    ch = logging.StreamHandler()
    ch.setLevel(logLevel)
    logger.addHandler(ch)
    logger.setLevel(logLevel)

    if debug:
      logger.debug("Enabled debug level")
      logger.debug("-------------------")

    # After adding the separate command for "cost" (i.e. `isitfit cost analyze`)
    # putting a note here to notify user of new usage
    # Ideally, this code would be deprecated though
    if ctx.invoked_subcommand is None:
        # if still used without subcommands, notify user of new usage
        #from .cost import analyze as cost_analyze, optimize as cost_optimize
        #if optimize:
        #  ctx.invoke(cost_optimize, filter_tags=filter_tags, n=n)
        #else:
        #  ctx.invoke(cost_analyze, filter_tags=filter_tags)
        from click.exceptions import UsageError
        if optimize:
          err_msg = "As of version 0.11, please use `isitfit cost optimize` instead of `isitfit --optimize`."
          ping_matomo("/error/UsageError?message=%s"%err_msg)
          raise UsageError(err_msg)
        elif version:
          # ctx.invoke(cli_version)
          err_msg = "As of version 0.11, please use `isitfit version` instead of `isitfit --version`."
          ping_matomo("/error/UsageError?message=%s"%err_msg)
          raise UsageError(err_msg)
        else:
          err_msg = "As of version 0.11, please use `isitfit cost analyze` instead of `isitfit` to calculate the cost-weighted utilization."
          ping_matomo("/error/UsageError?message=%s"%err_msg)
          raise UsageError(err_msg)

    # check if emailing requested
    if share_email is not None:
      max_n_recipients = 3
      if len(share_email) > max_n_recipients:
          err_msg = "Maximum allowed number of email recipients is %i. Received %i"%(max_n_recipients, len(share_email))
          ping_matomo("/error?message=%s"%err_msg)
          from click.exceptions import BadParameter
          raise BadParameter(err_msg, param_hint="--share-email")

      ctx.obj['share_email'] = share_email

    # check if current version is out-of-date
    if ctx.invoked_subcommand != 'version':
      if not skip_check_upgrade:
        from ..utils import prompt_upgrade
        is_outdated = prompt_upgrade('isitfit', isitfit_version)
        ctx.obj['is_outdated'] = is_outdated
        if is_outdated:
          ping_matomo("/version/prompt_upgrade?is_outdated=%s"%b2l(is_outdated))


    if ctx.invoked_subcommand not in ['version', 'migrations']:
      # run silent migrations
      from isitfit.migrations.migman import silent_migrate
      migname_l = silent_migrate()
      if len(migname_l)>0:
        from isitfit.utils import l2s
        migname_s = l2s(migname_l)
        ping_matomo("/migrations/silent?migname=%s"%(migname_s))

    # save `verbose` and `debug` for later tqdm
    ctx.obj['debug'] = debug
    ctx.obj['verbose'] = verbose
    # save skip-prompt-email for later usage
    ctx.obj['skip_prompt_email'] = skip_prompt_email



from .tags import tags as cli_tags
from .cost import cost as cli_cost
from .version import version as cli_version
from isitfit.migrations.cli import migrations as cli_migrations

cli_core.add_command(cli_version)
cli_core.add_command(cli_cost)
cli_core.add_command(cli_tags)
cli_core.add_command(cli_migrations)

#-----------------------

if __name__ == '__main__':
  cli_core()
