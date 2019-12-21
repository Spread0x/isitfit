# imports
import datetime as dt
from isitfit.utils import SECONDS_IN_ONE_DAY
import pandas as pd
import boto3

from isitfit.utils import logger, NoCloudwatchException


def raise_noCwExc(rc_id):
  raise NoCloudwatchException("No cloudwatch data for %s"%rc_id)


import numpy as np


class CloudwatchAssistant:
  """
  Manager for cloudwatch
  """

  def __init__(self):
    self.set_ndays(90) # default is 90 days


  def set_resource(self, region_name):
        """
        Easy-to-mock function since moto mock of cloudwatch is giving pagination error
        """
        boto3.setup_default_session(region_name = region_name)
        self.cloudwatch_resource = boto3.resource('cloudwatch')


  def id2iterator(self, rc_id, cloudwatch_namespace, entry_keyId):

    if cloudwatch_namespace is None:
      raise Exception("Derived class should set cloudwatch_namespace")

    metrics_iterator = self.cloudwatch_resource.metrics.filter(
        Namespace = cloudwatch_namespace,
        MetricName = 'CPUUtilization',
        Dimensions=[
            {'Name': entry_keyId, 'Value': rc_id},
        ]
      )
    return metrics_iterator


  def iterator2metric(self, metrics_iterator, rc_id):

    #logger.debug("redshift cluster details")
    #logger.debug(rc_describe_entry)

    for m_i in metrics_iterator:

        # skip node stats for now, and focus on cluster stats
        # i.e. dimensions only ClusterIdentifier, without the NodeID key
        if len(m_i.dimensions)>1:
          continue

        # exit the for loop and return this particular metric (cluster)
        return m_i

    # in case no cluster metrics found
    logger.debug("No cloudwatch metrics found for %s"%rc_id)
    raise_noCwExc(rc_id)


  def set_ndays(self, ndays):
    self.ndays = ndays

    # set start/end dates

    # FIXME? in mainManager, used pytz
    # dt_now_d=dt.datetime.now().replace(tzinfo=pytz.utc)
    dt_now_d = dt.datetime.utcnow()
    self.StartTime = dt_now_d - dt.timedelta(days=self.ndays)
    self.EndTime = dt_now_d

    # cloudwatch needs this to return the full data, including today?
    self.StartTime = self.StartTime.replace(hour=0, minute=0, second=0)
    self.EndTime = self.EndTime.replace(hour=23, minute=59, second=59)


  def metric2stats(self, metric):
    """
    For newly created instances, the Timestamp field is not reliable from here.
    It needs postprocessing by stats2df.
    For example, if today is 2019-12-17, an instance created today could return
    Timestamp=datetime.datetime(2019, 12, 13, 9, 0, tzinfo=tzutc())
    """
    logger.debug("fetch cw")
    logger.debug(metric.dimensions)

    # util func
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html#CloudWatch.Metric.get_statistics
    # https://docs.aws.amazon.com/redshift/latest/mgmt/metrics-listing.html
    #
    # Note for redshift cluster
    # remember that max for redshift cluster = max of stats of all nodes
    response = metric.get_statistics(
        Dimensions=metric.dimensions,
        StartTime=self.StartTime,
        EndTime=self.EndTime,
        Period=SECONDS_IN_ONE_DAY,
        Statistics=['Minimum', 'Average', 'Maximum', 'SampleCount'],
        Unit = 'Percent'
    )
    logger.debug(response)
    return response


  def stats2df(self, response_metric, rc_id, ClusterCreateTime, cloudwatch_namespace):
    if len(response_metric['Datapoints'])==0:
      raise_noCwExc(rc_id)

    # convert to dataframe
    df = pd.DataFrame(response_metric['Datapoints'])

    # edit 2019-09-13: no need to subsample columns
    # The initial goal was to drop the "Unit" column (which just said "Percent"),
    # but it's not such a big deal, and avoiding this subsampling simplifies the code a bit
    # df = df[['Timestamp', 'SampleCount', 'Average']]

    # sort and append in case of multiple metrics
    df = df.sort_values(['Timestamp'], ascending=True)

    # before returning, convert dateutil timezone to pytz
    # for https://github.com/pandas-dev/pandas/issues/25423
    # via https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.Series.dt.tz_convert.html
    # Edit 2019-09-25 Instead of keeping the full timestamp, just truncate to date, especially that this is just daily data
    # df['Timestamp'] = df.Timestamp.dt.tz_convert(pytz.utc)
    df['Timestamp'] = df.Timestamp.dt.date

    # cloudwatch bug: a newly created instance today will return a Timestamp before today
    # In this case, correcting the timestamp
    # Update 2019-12-17 This was fixed by setting the EndTime.hour,minute,second to the next midnight
    #if df.shape[0]==1:
    #  dt_now = dt.datetime.now().date()
    #  if ClusterCreateTime.date() == dt_now:
    #    if df.Timestamp.iloc[0] != dt_now:
    #      raise Exception("This cloudwatch bug was fixed by setting the hours/minutes/seconds of start/end time (location 1)")
    #      df.iloc[0, df.columns=='Timestamp'] = dt_now
    #
    ## drop points "before create time" (bug in cloudwatch?)
    ## Edit 2019-11-18 since this is daily data, and we don't really care about hours/minutes, just compare the y-m-d parts
    ## Update 2019-12-16 This is a weird bug
    #idx_cwbug = df['Timestamp'] >= ClusterCreateTime.date()
    #if not idx_cwbug.all():
    #  raise Exception("This cloudwatch bug was fixed by setting the hours/minutes/seconds of start/end time (location 2)")
    #  logger.debug("Cloudwatch bug of metric data after resource creation time: %s"%rc_id)

    #df = df[ idx_cwbug ]
    #if df.shape[0]==0: raise_noCwExc(rc_id)

    # calculate number of running hours
    # In the latest 90 days, sampling is per minute in cloudwatch
    # https://aws.amazon.com/cloudwatch/faqs/
    # Q: What is the minimum resolution for the data that Amazon CloudWatch receives and aggregates?
    # A: ... For example, if you request for 1-minute data for a day from 10 days ago, you will receive the 1440 data points ...
    if cloudwatch_namespace == 'AWS/EC2':
      df['nhours'] = np.ceil(df.SampleCount/60)
    elif cloudwatch_namespace == 'AWS/Redshift':
      # Redshift cloudwatch metrics are every 30 seconds (this seems to be the case by trial and error)
      # X points * 0.5 mins/point / 60 minutes/hr = Y hours
      df['nhours'] = np.ceil(df.SampleCount/60/2)

    # rename columns
    df.rename(columns={
        'Maximum': 'cpu_used_max',
        'Average': 'cpu_used_avg',
        'Minimum': 'cpu_used_min',
      },
      inplace=True
    )

    # append nan for memory
    df['ram_used_max'] = np.nan
    df['ram_used_avg'] = np.nan
    df['ram_used_min'] = np.nan

    logger.debug("returning dataframe.head")
    logger.debug(df.head())

    # print
    return df



class CloudwatchBase:
  cloudwatch_namespace = None
  entry_keyId = None

  def __init__(self):
    self.assistant = CloudwatchAssistant()

  def set_ndays(self, ndays):
    self.assistant.set_ndays(ndays)

  @property
  def ndays(self):
    """
    Expose the assistant.ndays member as a member here
    """
    return self.assistant.ndays

  def handle_main(self, rc_describe_entry, rc_id, rc_created):
    logger.debug("Fetching cloudwatch data for resource %s"%rc_id)

    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html#metric
    self.assistant.set_resource(region_name = rc_describe_entry['Region'])

    metrics_iterator = self.assistant.id2iterator(rc_id, self.cloudwatch_namespace, self.entry_keyId)

    # filter for 1 metric
    metric_single = self.assistant.iterator2metric(metrics_iterator, rc_id)
    response = self.assistant.metric2stats(metric_single)

    # dataframe of CPU Utilization, max and min, over 90 days
    df = self.assistant.stats2df(response, rc_id, rc_created, self.cloudwatch_namespace)

    return df


from .cacheManager import MetricCacheMixin


class CloudwatchCached(MetricCacheMixin, CloudwatchBase):
    """
    Manager for cloudwatch
    """

    def get_key(self, rc_id):
        # build key out of the same parameters in metric.get_statistics and metrics.filter
        #cache_key = "{Namespace}/{MetricName}/{DimensionName}/{DimensionValue}/{ndays}".format(
        #  Namespace = self.cloudwatch_namespace,
        #  MetricName = 'CPUUtilization',
        #  DimensionName = self.entry_keyId,
        #  DimensionValue = rc_id,
        #  ndays = self.ndays
        #)

        # KISS for now
        cache_key = "cloudwatch:cpu:%s:%i"%(rc_id, self.ndays)
        return cache_key

    def get_metrics_base(self, rc_describe_entry, rc_id, rc_created):
      return self.handle_main(rc_describe_entry, rc_id, rc_created)



class CloudwatchRedshift(CloudwatchCached):
  cloudwatch_namespace = 'AWS/Redshift'
  entry_keyId = 'ClusterIdentifier'


class CwRedshiftListener(CloudwatchRedshift):
  """
  Not yet deprecated
  AFAIK the datdog-redshift integration doesn't include memory metrics [1]
  So just referencing CwRedshiftListener in the redshift pipeline

  [1] https://docs.datadoghq.com/integrations/amazon_redshift/
  """
  def per_ec2(self, context_ec2):
        """
        Raises NoCloudwatchException if no data found in cloudwatch
        """
        rc_describe_entry, rc_id, rc_created = context_ec2['ec2_dict'], context_ec2['ec2_id'], context_ec2['ec2_launchtime']
        try:
          df_single = self.get_metrics_derived(rc_describe_entry, rc_id, rc_created)
          context_ec2['df_single'] = df_single
          return context_ec2
        except NoCloudwatchException:
          # Break chain of listeners
          # context_ec2['df_single'] = None
          return None




class CloudwatchEc2(CloudwatchCached):
  cloudwatch_namespace = 'AWS/EC2'
  entry_keyId = 'InstanceId'


class CwEc2Listener(CloudwatchEc2):
  """
  Deprecated in favor of metrics_automatic which references CloudwatchEc2 itself
  """

  def handle_main(self, ec2_obj):
    raise Exception("Deprecated")

    df_cw3 = super().handle_main({'Region': ec2_obj.region_name}, ec2_obj.instance_id, ec2_obj.launch_time)
    return df_cw3

  def per_ec2(self, context_ec2):
    """
    Raises NoCloudwatchException if no data found in cloudwatch
    """
    raise Exception("Deprecated")

    ec2_obj = context_ec2['ec2_obj']
    try:
      df_cw3 = self.handle_main(ec2_obj)
      context_ec2['df_metrics'] = df_cw3
      return context_ec2
    except NoCloudwatchException:
      # Break chain of listeners
      # context_ec2['df_metrics'] = None
      return None


