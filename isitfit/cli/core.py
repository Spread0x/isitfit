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

@click.group(invoke_without_command=True)
@click.option('--debug', is_flag=True, help='Display more details to help with debugging')
@click.option('--optimize', is_flag=True, help='DEPRECATED: get cost optimization recommendations')
@click.option('--share-email', default=None, help='Share result to email address')
@click.pass_context
def cli_core(ctx, debug, optimize, share_email):

    logLevel = logging.DEBUG if debug else logging.INFO
    ch = logging.StreamHandler()
    ch.setLevel(logLevel)
    logger.addHandler(ch)
    logger.setLevel(logLevel)

    if debug:
      logger.debug("Enabled debug level")
      logger.debug("-------------------")

    # check if current version is out-of-date
    from ..utils import prompt_upgrade
    is_outdated = prompt_upgrade('isitfit', isitfit_version)
    if is_outdated:
      # Give the user some time to read the message and possibly update
      import time
      time.sleep(3)

    # make sure that context is a dict
    ctx.ensure_object(dict)

    # check if emailing requested
    if share_email is not None:
      ctx.obj['share_email'] = share_email

    # After adding the separate command for "cost" (i.e. `isitfit cost analyze`)
    # putting a note here to notify user of new usage
    # Ideally, this code would be deprecated though

    # if a command is invoked, eg `isitfit tags`, do not proceed
    if ctx.invoked_subcommand is not None:
      return

    # if still used without subcommands, notify user of new usage
    #from .cost import analyze as cost_analyze, optimize as cost_optimize
    #if optimize:
    #  ctx.invoke(cost_optimize, filter_tags=filter_tags, n=n)
    #else:
    #  ctx.invoke(cost_analyze, filter_tags=filter_tags)
    if optimize:
      click.secho("Deprecation note as of version 0.11:", fg='red')
      click.secho("  Please use `isitfit cost optimize` instead of `isitfit --optimize`.", fg='red')
    else:
      click.secho("Deprecation note as of version 0.11:", fg='red')
      click.secho("  Please use `isitfit cost analyze` instead of `isitfit` to calculate the cost-weighted utilization.", fg='red')

    # just return non-0 code
    import sys
    sys.exit(1)


from .tags import tags as cli_tags
from .cost import cost as cli_cost
from .version import version as cli_version

cli_core.add_command(cli_version)
cli_core.add_command(cli_cost)
cli_core.add_command(cli_tags)

#-----------------------

if __name__ == '__main__':
  cli_core()
