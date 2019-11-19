# imports
import datetime as dt
from ...utils import SECONDS_IN_ONE_DAY
import pandas as pd
import boto3

from isitfit.utils import raise_noCwExc, NoCloudwatchException, myreturn

import logging
logger = logging.getLogger('isitfit')


class CloudwatchBase:
  """
  Manager for cloudwatch
  """

  cloudwatch_namespace = None
  entry_keyId = None


  def __init__(self):
    self._initDates()


  def _initDates(self):
    # set start/end dates
    N_DAYS=90

    # FIXME? in mainManager, used pytz
    # dt_now_d=dt.datetime.now().replace(tzinfo=pytz.utc)
    dt_now_d = dt.datetime.utcnow()
    self.StartTime = dt_now_d - dt.timedelta(days=N_DAYS)
    self.EndTime = dt_now_d


  def _metric_get_statistics(self, metric):
    logger.debug("fetch cw")
    logger.debug(metric.dimensions)

    # util func
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html#CloudWatch.Metric.get_statistics
    # https://docs.aws.amazon.com/redshift/latest/mgmt/metrics-listing.html
    response = metric.get_statistics(
        Dimensions=metric.dimensions,
        StartTime=self.StartTime,
        EndTime=self.EndTime,
        Period=SECONDS_IN_ONE_DAY,
        Statistics=['Minimum', 'Average', 'Maximum', 'SampleCount'],
        Unit = 'Percent'
    )
    return response


  def _metrics_filter(self, rc_id):
    if self.cloudwatch_namespace is None:
      raise Exception("Derived class should set cloudwatch_namespace")

    metrics_iterator = self.cloudwatch_resource.metrics.filter(
        Namespace = self.cloudwatch_namespace,
        MetricName = 'CPUUtilization',
        Dimensions=[
            {'Name': self.entry_keyId, 'Value': rc_id},
        ]
      )
    return metrics_iterator


  def handle_cluster(self, rc_id):

    #logger.debug("redshift cluster details")
    #logger.debug(rc_describe_entry)

    # remember that max for cluster = max of stats of all nodes
    logger.debug("Getting cloudwatch for cluster: %s"%(rc_id))
    metrics_iterator = self._metrics_filter(rc_id)
    for m_i in metrics_iterator:
        # skip node stats for now, and focus on cluster stats
        # i.e. dimensions only ClusterIdentifier, without the NodeID key
        if len(m_i.dimensions)>1:
          continue

        # exit the for loop and return this particular metric (cluster)
        return m_i

    # in case no cluster metrics found
    raise_noCwExc(rc_id)



  def handle_metric(self, m_i, rc_id, ClusterCreateTime):
    response_metric = self._metric_get_statistics(m_i)

    logger.debug("cw response_metric for %s"%rc_id)
    logger.debug(response_metric)

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

    # drop points "before create time" (bug in cloudwatch?)
    # Edit 2019-11-18 since this is daily data, and we don't really care about hours/minutes, just compare the y-m-d parts
    df = df[ df['Timestamp'] >= ClusterCreateTime.date() ]

    # print
    return df


  def _cloudwatch_metrics_boto3(self, region_name):
        """
        Easy-to-mock function since moto mock of cloudwatch is giving pagination error
        """
        boto3.setup_default_session(region_name = region_name)
        cloudwatch_resource = boto3.resource('cloudwatch')
        return cloudwatch_resource


  def handle_main(self, rc_describe_entry, rc_id, rc_created):
        logger.debug("Found cluster %s"%rc_id)

        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html#metric
        self.cloudwatch_resource = self._cloudwatch_metrics_boto3(region_name = rc_describe_entry['Region'])

        # get metric
        m_i = self.handle_cluster(rc_id)

        # dataframe of CPU Utilization, max and min, over 90 days
        df = self.handle_metric(m_i, rc_id, rc_created)

        logger.debug("returning dataframe.head")
        logger.debug(df.head())

        return df


class CloudwatchCached(CloudwatchBase):
  def __init__(self, cache_man=None):
    """
    cache_man - from .cacheManager import RedisPandas as RedisPandasCacheManager

    """
    # manager of redis-pandas caching
    self.cache_man = cache_man
    super().__init__()


  def handle_main(self, rc_describe_entry, rc_id, rc_created):
        cache_key = "mainManager._cloudwatch_metrics/%s"%rc_id

        # in case of no cache
        if self.cache_man is None:
          df_fresh = super().handle_main(rc_describe_entry, rc_id, rc_created)
          return df_fresh

        # check cache first
        if self.cache_man.isReady():
          df_cache = self.cache_man.get(cache_key)
          if df_cache is not None:
            logger.debug("Found cloudwatch metrics in redis cache for %s, and data.shape[0] = %i"%(rc_id, df_cache.shape[0]))
            df_ret = myreturn(df_cache)
            if df_ret is None: raise_noCwExc(rc_id)
            if df_ret.shape[0]==0: raise_noCwExc(rc_id)
            return df_ret

        # if no cache, then download
        should_raise = False
        try:
          df_fresh = super().handle_main(rc_describe_entry, rc_id, rc_created)
        except NoCloudwatchException as e:
          df_fresh = pd.DataFrame()
          should_raise = True

        # if caching enabled, store it for later fetching
        # https://stackoverflow.com/a/57986261/4126114
        # Note that this even stores the result if it was "None" (meaning that no data was found)
        if self.cache_man.isReady():
          self.cache_man.set(cache_key, df_fresh)

        # check if should raise
        if should_raise:
          raise_noCwExc(rc_id)

        # done
        df_ret = myreturn(df_fresh)
        if df_ret is None: raise_noCwExc(rc_id)
        if df_ret.shape[0]==0: raise_noCwExc(rc_id)
        return df_ret



class CloudwatchRedshift(CloudwatchCached):
  cloudwatch_namespace = 'AWS/Redshift'
  entry_keyId = 'ClusterIdentifier'

  def per_ec2(self, context_ec2):
        """
        Raises NoCloudwatchException if no data found in cloudwatch
        """
        rc_describe_entry, rc_id, rc_created = context_ec2['ec2_dict'], context_ec2['ec2_id'], context_ec2['ec2_launchtime']
        df_single = self.handle_main(rc_describe_entry, rc_id, rc_created)
        context_ec2['df_single'] = df_single
        return context_ec2



class CloudwatchEc2(CloudwatchCached):
  cloudwatch_namespace = 'AWS/EC2'
  entry_keyId = 'InstanceId'

  def per_ec2(self, context_ec2):
        """
        Raises NoCloudwatchException if no data found in cloudwatch
        """
        ec2_obj = context_ec2['ec2_obj']
        df_cw3 = self.handle_main({'Region': ec2_obj.region_name}, ec2_obj.instance_id, ec2_obj.launch_time)
        context_ec2['df_metrics'] = df_cw3
        return context_ec2

