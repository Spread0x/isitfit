# RuntimeError: Click will abort further execution because Python 3 was configured to use ASCII as encoding for the environment.
# Consult https://click.palletsprojects.com/en/7.x/python3/ for mitigation steps.
#
# Edit 2019-10-08: whatsapp's wadebug uses "click.disable_unicode_literals_warning = True"
# Ref: https://github.com/WhatsApp/WADebug/blob/958ac37be804cc732ae514d4872b93d19d197a5c/wadebug/cli.py#L23
from ..utils import mysetlocale
mysetlocale()


import logging
logger = logging.getLogger('isitfit')

import click

from ..utils import display_footer
from .. import isitfit_version


# With atexit, this message is being displayed even in case of early return or errors.
# Changing to try/finally in the __main__ below
#import atexit
#atexit.register(display_footer)

# For the --share-email "multiple options"
# https://click.palletsprojects.com/en/7.x/options/#multiple-options

@click.group(invoke_without_command=True)
@click.option('--debug', is_flag=True, help='Display more details to help with debugging')
@click.option('--optimize', is_flag=True, help='DEPRECATED: use "isitfit cost optimize" instead')
@click.option('--version', is_flag=True, help='DEPRECATED: use "isitfit version" instead')
@click.option('--share-email', multiple=True, help='Share result to email address')
@click.option('--skip-check-update', is_flag=True, help='Skip step for checking for update')
@click.pass_context
def cli_core(ctx, debug, optimize, version, share_email, skip_check_update):
    logLevel = logging.DEBUG if debug else logging.INFO
    ch = logging.StreamHandler()
    ch.setLevel(logLevel)
    logger.addHandler(ch)
    logger.setLevel(logLevel)

    if debug:
      logger.debug("Enabled debug level")
      logger.debug("-------------------")

    # if a command is invoked, eg `isitfit tags`, do not proceed
    if ctx.invoked_subcommand is None:
        # if still used without subcommands, notify user of new usage
        #from .cost import analyze as cost_analyze, optimize as cost_optimize
        #if optimize:
        #  ctx.invoke(cost_optimize, filter_tags=filter_tags, n=n)
        #else:
        #  ctx.invoke(cost_analyze, filter_tags=filter_tags)
        if optimize:
          click.secho("As of version 0.11, please use `isitfit cost optimize` instead of `isitfit --optimize`.", fg='red')
        else:
          click.secho("As of version 0.11, please use `isitfit cost analyze` instead of `isitfit` to calculate the cost-weighted utilization.", fg='red')

        # just return non-0 code
        import sys
        sys.exit(1)

    # check if current version is out-of-date
    if not skip_check_update:
      from ..utils import prompt_upgrade
      prompt_upgrade('isitfit', isitfit_version)

    # make sure that context is a dict
    ctx.ensure_object(dict)

    # check if emailing requested
    if share_email is not None:
      ctx.obj['share_email'] = share_email

    # Important that this be "after" the check for update
    if version:
        # ctx.invoke(cli_version)
        click.secho("As of version 0.11, please use `isitfit version` instead of `isitfit --version`.", fg='red')
        import sys
        sys.exit(1)

    # After adding the separate command for "cost" (i.e. `isitfit cost analyze`)
    # putting a note here to notify user of new usage
    # Ideally, this code would be deprecated though



from .tags import tags as cli_tags
from .cost import cost as cli_cost
from .version import version as cli_version

cli_core.add_command(cli_version)
cli_core.add_command(cli_cost)
cli_core.add_command(cli_tags)

#-----------------------

if __name__ == '__main__':
  cli_core()
