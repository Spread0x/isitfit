# imports
import datetime as dt
from ...utils import SECONDS_IN_ONE_DAY
import pandas as pd

import logging
logger = logging.getLogger('isitfit')


class BaseIterator:
  """
  Iterator design pattern
  Iterates over all CPU performance dataframes
  https://en.wikipedia.org/wiki/Iterator_pattern#Python
  """

  cloudwatch_namespace = None
  service_name = None
  service_description = None
  paginator_name = None
  paginator_entryJmespath = None
  paginator_exception = None
  entry_keyId = None
  entry_keyCreated = None


  def __init__(self):
    self._initDates()

    # list of cluster ID's for which data is not available
    self.rc_noData = []

    # list of regions to skip
    self.region_include = []

    # in case of just_count=True, region_include is ignored since it is not yet populated
    # Set this flag to use region_include, eg if it is loaded from cache or if counting first pass is done
    self.regionInclude_ready = False

    # init cache
    self._initCache()


  def _initCache(self):
    """
    # try to load region_include from cache
    """

    # need to use the profile name
    # because a profile could have ec2 in us-east-1
    # whereas another could have ec2 in us-west-1
    import boto3
    profile_name = boto3.session.Session().profile_name

    # cache filename and key to use
    from ...dotMan import DotMan
    import os
    self.cache_filename = 'iterator_cache-%s-%s.pkl'%(profile_name, self.service_name)
    self.cache_filename = os.path.join(DotMan().get_dotisitfit(), self.cache_filename)

    self.cache_key = 'iterator-region_include'

    # https://github.com/barisumog/simple_cache
    import simple_cache
    ri_cached = simple_cache.load_key(filename=self.cache_filename, key=self.cache_key)
    if ri_cached is not None:
      logger.debug("Loading regions containing EC2 from cache file")
      self.region_include = ri_cached
      self.regionInclude_ready = True


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
        Statistics=['Minimum', 'Average', 'Maximum'],
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
      self.rc_noData.append(rc_id)
      return None

    # convert to dataframe
    df = pd.DataFrame(response_metric['Datapoints'])

    # drop points "before create time" (bug in cloudwatch?)
    df = df[ df['Timestamp'] >= ClusterCreateTime ]

    # print
    return df


  def iterate_core(self, just_counting=False, display_tqdm=False):
    fx_l = ['service_name', 'service_description', 'paginator_name', 'paginator_entryJmespath', 'paginator_exception', 'entry_keyId', 'entry_keyCreated']
    for fx_i in fx_l:
      # https://stackoverflow.com/a/9058315/4126114
      if fx_i not in self.__class__.__dict__.keys():
        raise Exception("Derived class should set %s"%fx_i)

    # iterate on regions
    import botocore
    import boto3
    import jmespath
    redshift_regions = boto3.Session().get_available_regions(self.service_name)
    # redshift_regions = ['us-west-2'] # FIXME

    region_iterator = redshift_regions
    if just_counting and display_tqdm:
      from tqdm import tqdm
      region_iterator = tqdm(region_iterator, total = len(redshift_regions), desc="%s, counting in all regions"%self.service_description)

    for region_name in region_iterator:
      if self.regionInclude_ready:
        if region_name not in self.region_include:
          # skip since already failed to use it
          continue

      logger.debug("Region %s"%region_name)
      boto3.setup_default_session(region_name = region_name)

      # boto3 clients
      # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/redshift.html#Redshift.Client.describe_logging_status
      redshift_client = boto3.client(self.service_name)

      # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html#metric
      self.cloudwatch_resource = boto3.resource('cloudwatch')

      # iterate on redshift clusters
      paginator = redshift_client.get_paginator(self.paginator_name)
      rc_iterator = paginator.paginate()
      try:
        region_anyClusterFound = False
        for rc_describe_page in rc_iterator:
          rc_describe_entries = jmespath.search(self.paginator_entryJmespath, rc_describe_page)
          for rc_describe_entry in rc_describe_entries:
            region_anyClusterFound = True
            # add field for region
            rc_describe_entry['Region'] = region_name
            # yield
            yield rc_describe_entry

        if not self.regionInclude_ready:
          if region_anyClusterFound:
            # only include if found clusters in this region
            self.region_include.append(region_name)

      except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code']==self.paginator_exception:
          continue

        # all other exceptions raised
        raise e

    # before exiting, check if a count just completed, and mark region_include as usable
    if just_counting:
      self.regionInclude_ready = True

      # save to cache
      import simple_cache
      SECONDS_PER_HOUR = 60*60
      simple_cache.save_key(filename=self.cache_filename, key=self.cache_key, value=self.region_include, ttl=SECONDS_PER_HOUR)



  def __iter__(self):
    for rc_describe_entry in self.iterate_core(False, False):
        #print("response, entry")
        #print(rc_describe_entry)

        # if not available yet (eg creating), still include analysis in case of past data
        #if rc_describe_entry['ClusterStatus'] != 'available':
        #    self.rc_noData.append(rc_id)
        #    continue

        if self.entry_keyId not in rc_describe_entry:
          # no ID, weird
          continue

        rc_id = rc_describe_entry[self.entry_keyId]

        if self.entry_keyCreated not in rc_describe_entry:
          # no creation time yet, maybe in process
          self.rc_noData.append(rc_id)
          continue

        rc_created = rc_describe_entry[self.entry_keyCreated]
        logger.debug("Found cluster %s"%rc_id)
        m_i = self.handle_cluster(rc_id)

        # no metrics for cluster, skip
        if m_i is None:
            self.rc_noData.append(rc_id)
            continue

        # dataframe of CPU Utilization, max and min, over 90 days
        df = self.handle_metric(m_i, rc_id, rc_created)


        yield rc_describe_entry, df



class RedshiftPerformanceIterator(BaseIterator):
  cloudwatch_namespace = 'AWS/Redshift'
  service_name = 'redshift'
  service_description = 'Redshift clusters'
  paginator_name = 'describe_clusters'
  paginator_entryJmespath = 'Clusters[]'
  paginator_exception = 'InvalidClientTokenId'
  entry_keyId = 'ClusterIdentifier'
  entry_keyCreated = 'ClusterCreateTime'


class Ec2Iterator(BaseIterator):
  cloudwatch_namespace = 'AWS/EC2'
  service_name = 'ec2'
  service_description = 'EC2 instances'
  paginator_name = 'describe_instances'
  # Notice that [] notation flattens the list of lists
  # http://jmespath.org/tutorial.html
  paginator_entryJmespath = 'Reservations[].Instances[]'
  paginator_exception = 'AuthFailure'
  entry_keyId = 'InstanceId'
  entry_keyCreated = 'LaunchTime'

