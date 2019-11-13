# imports
import boto3
import datetime as dt
from ...utils import SECONDS_IN_ONE_DAY
import pandas as pd

import logging
logger = logging.getLogger('isitfit')


class RedshiftPerformanceIterator:
  """
  Iterator design pattern
  Iterates over all CPU performance dataframes
  https://en.wikipedia.org/wiki/Iterator_pattern#Python
  """

  # list of cluster ID's for which data is not available
  rc_noData = []


  def __init__(self):
    self._initDates()
    self._initBoto3()


  def _initDates(self):
    # set start/end dates
    N_DAYS=90

    # FIXME? in mainManager, used pytz
    # dt_now_d=dt.datetime.now().replace(tzinfo=pytz.utc)
    dt_now_d = dt.datetime.utcnow()
    self.StartTime = dt_now_d - dt.timedelta(days=N_DAYS)
    self.EndTime = dt_now_d


  def _initBoto3(self):
    # boto3 clients
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/redshift.html#Redshift.Client.describe_logging_status
    self.redshift_client = boto3.client('redshift')
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html#metric
    self.cloudwatch_resource = boto3.resource('cloudwatch')


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
        Statistics=['Minimum', 'Average', 'Maximum'],
        Unit = 'Percent'
    )
    return response


  def _metrics_filter(self, rc_id):
    metrics_iterator = self.cloudwatch_resource.metrics.filter(
        Namespace = 'AWS/Redshift',
        MetricName = 'CPUUtilization',
        Dimensions=[
            {'Name': 'ClusterIdentifier', 'Value': rc_id},
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
    return None


  def handle_metric(self, m_i, rc_id, ClusterCreateTime):
    response_metric = self._metric_get_statistics(m_i)
    logger.debug("cw response_metric")
    #logger.debug(response_metric)

    if len(response_metric['Datapoints'])==0:
      self.rc_noData.append(rc_id)
      return None

    # convert to dataframe
    df = pd.DataFrame(response_metric['Datapoints'])

    # drop points "before create time" (bug in cloudwatch?)
    df = df[ df['Timestamp'] >= ClusterCreateTime ]

    # print
    return df


  def iterate_core(self):
    # iterate on redshift clusters
    paginator = self.redshift_client.get_paginator('describe_clusters')
    rc_iterator = paginator.paginate()
    for rc_describe_page in rc_iterator:
      for rc_describe_entry in rc_describe_page['Clusters']:
        yield rc_describe_entry


  def __iter__(self):
    for rc_describe_entry in self.iterate_core():
        #print("response, entry")
        #print(rc_describe_entry)

        # if not available yet (eg creating), still include analysis in case of past data
        #if rc_describe_entry['ClusterStatus'] != 'available':
        #    self.rc_noData.append(rc_id)
        #    continue

        if 'ClusterIdentifier' not in rc_describe_entry:
          # no ID, weird
          continue

        rc_id = rc_describe_entry['ClusterIdentifier']

        if 'ClusterCreateTime' not in rc_describe_entry:
          # no creation time yet, maybe in process
          self.rc_noData.append(rc_id)
          continue

        rc_created = rc_describe_entry['ClusterCreateTime']
        logger.debug("Found cluster %s"%rc_id)
        m_i = self.handle_cluster(rc_id)

        # no metrics for cluster, skip
        if m_i is None:
            self.rc_noData.append(rc_id)
            continue

        # dataframe of CPU Utilization, max and min, over 90 days
        df = self.handle_metric(m_i, rc_id, rc_created)


        yield rc_describe_entry, df
