def mergeSeriesOnTimestampRange(df_cpu, df_type):
  """
  Upsamples df_type to df_cpu.
  Example:
    Input
      df_cpu = pd.Series({'time': [1,2,3,4], 'field_1': [5,6,7,8]})
      df_type = pd.Series({'time': [1,3], 'field_2': ['a','b']})
    Returns
      pd.Series({'time': [1,2,3,4], 'field_1': [5,6,7,8], 'field_2': ['a','a','b','b']})
  """
  import numpy as np

  df_cpu['instanceType'] = None
  # assume df_type is sorted in decreasing EventTime order (very important)
  # NB: since some instances are not present in the cloudtrail (for which we append artificially the "now" type)
  #     Need to traverse the df_type matrix backwards
  for index, row_type in df_type.iterrows():
      # use row_type.name instead of row_type['EventTime']
      # check note above about needing to traverse backwards
      # df_cpu.iloc[np.where(df_cpu.Timestamp >= row_type.name)[0], df_cpu.columns.get_loc('instanceType')] = row_type['instanceType']
      df_cpu.iloc[np.where(df_cpu.Timestamp <= row_type.name)[0], df_cpu.columns.get_loc('instanceType')] = row_type['instanceType']

  # fill na at beginning with back-fill
  # (artifact of cloudwatch having data at days before the creation of the instance)
  df_cpu['instanceType'] = df_cpu['instanceType'].fillna(method='backfill')
  return df_cpu







def ec2_catalog():
    import requests
    from cachecontrol import CacheControl
    from cachecontrol.caches.file_cache import FileCache

    import logging
    logger = logging.getLogger('isitfit')
    logger.debug("Downloading ec2 catalog (cached to local file)")

    # based on URL = 'http://www.ec2instances.info/instances.json'
    # URL = 's3://...csv'
    # Edit 2019-09-10 use CDN link instead of direct gitlab link
    # URL = 'https://gitlab.com/autofitcloud/www.ec2instances.info-ec2op/raw/master/www.ec2instances.info/t3b_smaller_familyL2.json'
    URL = 'https://cdn.jsdelivr.net/gh/autofitcloud/www.ec2instances.info-ec2op/www.ec2instances.info/t3b_smaller_familyL2.json'

    # cached https://cachecontrol.readthedocs.io/en/latest/
    sess = requests.session()
    cached_sess = CacheControl(sess, cache=FileCache('/tmp/isitfit_ec2info.cache'))
    r = cached_sess.request('get', URL)

    # read catalog, copy from ec2op-cli/ec2op/optimizer/cwDailyMaxMaxCpu
    import json
    j = json.dumps(r.json(), indent=4, sort_keys=True)
    from pandas import read_json
    df = read_json(j, orient='split')
    
    # Edit 2019-09-13 no need to subsample the columns at this stage
    # df = df[['API Name', 'Linux On Demand cost']]

    df = df.rename(columns={'Linux On Demand cost': 'cost_hourly'})
    # df = df.set_index('API Name') # need to use merge, not index
    return df


# copied from git-remote-aws
def mysetlocale():
  li = 'en_US.utf8'
  import os
  os.environ["LC_ALL"] = li
  os.environ["LANG"]   = li




MAX_ROWS = 10
MAX_COLS = 5
MAX_STRING = 20
def display_df(title, df, csv_fn, shape, logger):
    # https://pypi.org/project/termcolor/
    from termcolor import colored

    logger.info("")

    if shape[0]==0:
      logger.info(title)
      logger.info(colored("None", "red"))
      return

    if csv_fn is not None:
      logger.info(colored("The table '%s' was saved to the CSV file '%s'."%(title, csv_fn), "cyan"))
      logger.info(colored("It could be opened in the terminal with visidata (http://visidata.org/)","cyan"))
      logger.info(colored("and you can close visidata by pressing 'q'","cyan"))
      open_vd = input(colored('Would you like to do so? yes/[no] ', 'cyan'))
      if open_vd.lower() == 'yes' or open_vd.lower() == 'y':
        logger.info("Opening CSV file `%s` with visidata."%csv_fn)
        from subprocess import call
        call(["vd", csv_fn])
        logger.info("Exited visidata.")
        logger.info(colored("The table '%s' was saved to the CSV file '%s'."%(title, csv_fn), "cyan"))
        return
      else:
        logger.info("Not opening visidata.")
        logger.info("To open the results with visidata, use `vd %s`."%csv_fn)


    # if not requested to open with visidata
    from tabulate import tabulate
    df_show = df.head(n=MAX_ROWS)
    df_show = df_show.applymap(lambda c: (c[:MAX_STRING]+'...' if len(c)>=MAX_STRING else c) if type(c)==str else c)

    logger.info(tabulate(df_show, headers='keys', tablefmt='psql', showindex=False))

    if (shape[0] > MAX_ROWS) or (shape[1] > MAX_COLS):
      logger.info("...")
      logger.info("(results truncated)")
      # done
      return

    # done
    return


# Inherit from click's usageError since click can handle it automatically
# https://click.palletsprojects.com/en/7.x/exceptions/
from click import UsageError
class IsitfitCliError(UsageError):
  """
  Inherited from click.exceptions.UsageError
  because it adds the context as a constructor argument,
  which I need for checking "is_outdated"
  https://github.com/pallets/click/blob/8df9a6b2847b23de5c65dcb16f715a7691c60743/click/exceptions.py#L51
  """

  # exit code
  exit_code = 10

  # constructor parameters from
  # https://github.com/pallets/click/blob/8df9a6b2847b23de5c65dcb16f715a7691c60743/click/exceptions.py#L11
  def show(self, file=None):
    # ping matomo about error
    ping_matomo("/error?message=%s"%self.message)

    # continue
    from click._compat import get_text_stderr
    if file is None:
        file = get_text_stderr()

    # echo wrap
    color = 'red'
    import click
    def echo(message):
      # from click.utils import echo
      # echo('Error: %s' % self.format_message(), file=file, color=color)

      click.secho(message, fg=color)

    # main error
    echo('Error: %s' % self.format_message())

    # if isitfit installation is outdated, append a message to upgrade
    if self.ctx is not None:
      if self.ctx.obj.get('is_outdated', None):
        hint_1 = "Upgrade your isitfit installation with `pip3 install --upgrade isitfit` and try again."
        echo(hint_1)

    # add link to github issues
    hint_2 = "If the problem persists, please report it at https://github.com/autofitcloud/isitfit/issues/new"
    echo(hint_2)



def prompt_upgrade(pkg_name, current_version):
  """
  check if current version is out-of-date
  https://github.com/alexmojaki/outdated

  copied from https://github.com/WhatsApp/WADebug/blob/958ac37be804cc732ae514d4872b93d19d197a5c/wadebug/cli.py#L40
  """
  import outdated

  is_outdated = False
  try:
    is_outdated, latest_version = outdated.check_outdated(pkg_name, current_version)
  except ValueError as error:
    # catch case of "ValueError: Version 0.10.0 is greater than the latest version on PyPI: 0.9.1"
    # This would happen on my dev machine
    if not "is greater than" in str(error):
      raise

    # In this case, outdated does not cache the result to disk
    # so cache it myself (copied from https://github.com/alexmojaki/outdated/blob/565bb3fe1adc30da5e50249912cd2ac494662659/outdated/__init__.py#L61)
    latest_version = str(error).split(":")[1].strip()
    import datetime as dt
    import json
    with outdated.utils.cache_file(pkg_name, 'w') as f:
      try:
        data = [latest_version, outdated.utils.format_date(dt.datetime.now())]
        json.dump(data, f)
      except Exception as e:
        print('Error: ' + str(e))
        raise


  # is_outdated = True # FIXME for debugging
  if not is_outdated:
      return is_outdated

  import click
  msg_outdated = """The current version of {pkg_name} ({current_version}) is out of date.
Run `pip3 install {pkg_name} --upgrade` to upgrade to version {latest_version},
or use `isitfit --skip-check-upgrade ...` to skip checking for version upgrades of isitfit.
"""
  msg_outdated = msg_outdated.format(
      pkg_name=pkg_name, current_version=current_version, latest_version=latest_version
    )
  click.secho(msg_outdated, fg="red")

  # Give the user some time to read the message and possibly update
  import time
  from tqdm import tqdm
  wait_outdated = 10
  click.secho("Will continue in %i seconds"%wait_outdated, fg='yellow')
  for i in tqdm(range(wait_outdated)):
    time.sleep(1)

  return is_outdated


# This import needs to stay here for the sake of the mock in test_utils
import requests
SKIP_PING=False
def ping_matomo(action_name, uuid_val=None, isitfit_version=None):
  """
  Gather anonymous usage statistics
  """
  # get uuid
  from .dotMan import DotMan
  uuid_val = DotMan().get_myuid()

  # get version
  from . import isitfit_version as isitfit_cli_version

  # build action name field. note that "action_name" already starts with "/"
  full_actionName = "%s%s"%(isitfit_cli_version, action_name)

  # use base function
  from matomo_sdk_py.matomo_sdk_py import ping_matomo as ping_matomo_base
  ping_matomo_base(
    action_name=full_actionName,
    action_base="https://cli.isitfit.io",
    idsite=2, # 2 is for cli.isitfit.io
    uuid_val=uuid_val,
    matomo_url="https://isitfit.matomo.cloud/piwik.php"
  )


def display_footer():
    import logging
    logger = logging.getLogger('isitfit')

    from . import isitfit_version

    logger.info("")
    logger.info("⛅ Generated by isitfit version %s"%isitfit_version)
    logger.info("")
    logger.info("Useful links:")
    logger.info("ℹ️  isitfit homepage         https://isitfit.autofitcloud.com")
    logger.info("🌎 Global Climate Strike    https://twitter.com/hashtag/ClimateStrike")
    logger.info("❤️  Built by AutofitCloud    https://www.autofitcloud.com")



from click.core import Command as ClickCommand
class IsitfitCommand(ClickCommand):
    """
    Call display_footer at the end of each invokation
    https://github.com/pallets/click/blob/8df9a6b2847b23de5c65dcb16f715a7691c60743/click/core.py#L945
    """
    def invoke(self, *args, **kwargs):
        ret = super().invoke(*args, **kwargs)
        display_footer()
        return ret
