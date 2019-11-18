# imports
import datetime as dt
from ...utils import SECONDS_IN_ONE_DAY
import pandas as pd
import boto3

from isitfit.cost.mainManager import NoCloudwatchException

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
    return None


  def handle_metric(self, m_i, rc_id, ClusterCreateTime):
    response_metric = self._metric_get_statistics(m_i)
    #logger.debug("cw response_metric")
    #logger.debug(response_metric)

    if len(response_metric['Datapoints'])==0:
      raise NoCloudwatchException

    # convert to dataframe
    df = pd.DataFrame(response_metric['Datapoints'])

    # drop points "before create time" (bug in cloudwatch?)
    df = df[ df['Timestamp'] >= ClusterCreateTime ]

    # print
    return df

    
  def handle_main(self, rc_describe_entry, rc_id, rc_created):
        logger.debug("Found cluster %s"%rc_id)

        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html#metric
        region_name = rc_describe_entry['Region']
        boto3.setup_default_session(region_name = region_name)
        self.cloudwatch_resource = boto3.resource('cloudwatch')

        # get metric
        m_i = self.handle_cluster(rc_id)

        # no metrics for cluster, skip
        if m_i is None:
            raise NoCloudwatchException


        # dataframe of CPU Utilization, max and min, over 90 days
        df = self.handle_metric(m_i, rc_id, rc_created)

        return df



class CloudwatchRedshift(CloudwatchBase):
  cloudwatch_namespace = 'AWS/Redshift'
  entry_keyId = 'ClusterIdentifier'


class CloudwatchEc2(CloudwatchBase):
  cloudwatch_namespace = 'AWS/EC2'
  entry_keyId = 'InstanceId'

