from .metrics_datadog import HostNotFoundInDdg, DataNotFoundForHostInDdg
from .metrics_cloudwatch import NoCloudwatchException
from isitfit.utils import logger

class MetricsAuto:
  """
  Auto-fallback metrics fetching:
  If datadog credentials set in environment variable,
  try to get the metrics for a resource from datadog,
  otherwise fall back to cloudwatch
  """
  def __init__(self, datadog, cloudwatch):
    # class of instance metrics_datadog.DatadogCached
    self.datadog = datadog

    # class of instance metrics_cloudwatch.CloudwatchEc2 or CloudwatchRedshift
    self.cloudwatch = cloudwatch

    # dict with keys being host ID and value being
    # another dict with keys: ID, datadog, cloudwatch
    # and values being: host ID, status of fetching data from datadog, status of fetching data from cloudwatch
    self.status = {}


  def _try_datadog(self, host_id):
    if not self.datadog.is_configured():
      return None, "not configured"

    try:
      df_ddg = self.datadog.get_metrics_all(host_id)
      return df_ddg, "ok"
    except HostNotFoundInDdg as e:
      logger.debug("Datadog: host not found for %s: %s"%(host_id, str(e)))
      return None, "host not found"
    except DataNotFoundForHostInDdg as e:
      logger.debug("Datadog: data not found for %s: %s"%(host_id, str(e)))
      return None, "no data"


  def _try_cloudwatch(self, host_id, host_region, host_created):
    try:
      df_cw  = self.cloudwatch.handle_main({'Region': host_region}, host_id, host_created)
      return df_cw, "ok"
    except NoCloudwatchException:
      logger.debug("Cloudwatch: data not found for %s"%host_id)
      return None, "no data"


  def set_ndays(self, ndays):
    self.cloudwatch.set_ndays(ndays)
    self.datadog.set_ndays(ndays)


  def handle_host(self, host_id, host_region, host_created):
    logger.debug("host id, region, created: %s, %s, %s"%(host_id, host_region, host_created))

    self.status[host_id] = {
      'ID': host_id,
      'datadog': 'Did not try',
      'cloudwatch': 'Did not try'
    }
    df, status = self._try_datadog(host_id)
    self.status[host_id]['datadog'] = status
    if status!='ok':
      # "df is None" and status!=ok are equivalent
      df, status  = self._try_cloudwatch(host_id, host_region, host_created)
      self.status[host_id]['cloudwatch'] = status

    return df


  def display_status(self):
    # choose main function to display
    #from isitfit.utils import logger
    #display_msg = logger.info
    #import click
    #display_msg = click.echo

    # warning + color yellow
    from isitfit.utils import logger
    from termcolor import colored
    #display_msg = lambda x: colored(logger.warning(x), 'yellow')
    import click
    display_msg = lambda x: click.secho(x, fg='yellow')

    # inferred service
    from isitfit.cost.metrics_cloudwatch import CloudwatchEc2, CloudwatchRedshift
    service_map = {
      CloudwatchEc2: 'ec2',
      CloudwatchRedshift: 'redshift'
    }
    service_inferred = service_map.get(type(self.cloudwatch), 'unknown')

    # to dataframe
    import pandas as pd
    df = pd.DataFrame(self.status.values())

    if df.shape[0]==0:
      display_msg("")
      display_msg("Status of metric sources (for service %s)"%service_inferred)
      display_msg("<Empty table>")
      display_msg("")
      return

    df = df.sort_values(['ID'])
    gp = df.groupby(['datadog', 'cloudwatch']).count() # .reset_index().rename(columns={'ID': 'n'})
    from isitfit.dotMan import DotMan
    tempdir = DotMan().tempdir()
    import tempfile
    fh = tempfile.NamedTemporaryFile(prefix="isitfit-sourceStatus-", suffix='.csv', dir=tempdir, delete=False)
    df.to_csv(fh.name, index=False)

    # print with tabulate
    from tabulate import tabulate
    display_msg("")
    display_msg("Status of metric sources (for service %s)"%service_inferred)
    display_msg(tabulate(gp.reset_index(), tablefmt='psql', showindex=False, headers='keys'))
    display_msg("Details at %s"%fh.name)
    display_msg("")



class MetricsListener(MetricsAuto):
  """
  Listener for event bus defined in mainManager.py
  """
  def per_host(self, context_host):
    host_id = context_host['ec2_id']
    host_region, host_created = None, None

    ec2_obj = context_host['ec2_obj']
    if ec2_obj is not None:
      host_region = ec2_obj.region_name
      host_created = ec2_obj.launch_time

    df = self.handle_host(host_id, host_region, host_created)

    if df is None:
      # if still no data, just break the chain of listeners
      return None

    # otherwise if data is available
    context_host['df_metrics'] = df
    return context_host

  def display_status(self, context_all):
    super().display_status()
    return context_all
