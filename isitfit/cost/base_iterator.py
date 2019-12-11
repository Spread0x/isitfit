# imports
import datetime as dt
from isitfit.utils import SECONDS_IN_ONE_DAY
import pandas as pd

from isitfit.utils import logger


from isitfit.cli.click_descendents import IsitfitCliError


class BaseIterator:
  """
  Iterator design pattern
  Iterates over all CPU performance dataframes
  https://en.wikipedia.org/wiki/Iterator_pattern#Python
  """

  service_name = None
  service_description = None
  paginator_name = None
  paginator_entryJmespath = None
  paginator_exception = None
  entry_keyId = None
  entry_keyCreated = None


  def __init__(self, filter_region=None, tqdmman=None):
    # some defaults
    if tqdmman is None:
      from tqdm import tqdm
      tqdmman = tqdm

    # filter for certain region
    self.filter_region = filter_region

    # list of cluster ID's for which data is not available
    self.rc_noData = []

    # list of regions to skip
    self.region_include = []

    # in case of just_count=True, region_include is ignored since it is not yet populated
    # Set this flag to use region_include, eg if it is loaded from cache or if counting first pass is done
    self.regionInclude_ready = False

    # init cache
    self._initCache()

    # count of entries
    self.n_entry = None

    # handler of local tqdm
    self.tqdmman = tqdmman


  def get_regionInclude(self):
    """
    for the sake of mocking in the test tests/cost/redshift/test_cli.py:15
    """
    return self.region_include


  def _initCache(self):
    """
    # try to load region_include from cache
    """
    if self.filter_region is not None:
      self.region_include = [self.filter_region]
      self.regionInclude_ready = True
      return

    # need to use the profile name
    # because a profile could have ec2 in us-east-1
    # whereas another could have ec2 in us-west-1
    import boto3
    profile_name = boto3.session.Session().profile_name

    # cache filename and key to use
    # Update 2019-12-03: move from ~/.isitfit to /tmp/isitfit/
    from isitfit.dotMan import DotMan
    import os
    self.cache_filename = 'iterator_cache-%s-%s.pkl'%(profile_name, self.service_name)
    self.cache_filename = os.path.join(DotMan().tempdir(), self.cache_filename)

    # proceed with key
    self.cache_key = 'iterator-region_include'

    # https://github.com/barisumog/simple_cache
    import simple_cache
    ri_cached = simple_cache.load_key(filename=self.cache_filename, key=self.cache_key)
    if ri_cached is not None:
      logger.debug("Loading regions containing EC2 from cache file")
      self.region_include = ri_cached
      self.regionInclude_ready = True


  def iterate_core(self, display_tqdm=False):
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

    if self.filter_region is not None:
      if self.filter_region not in redshift_regions:
        msg_err = "Invalid region specified: %s. Supported values: %s"
        msg_err = msg_err%(self.filter_region, ", ".join(redshift_regions))
        raise IsitfitCliError(msg_err, None) # passing None for click context

      # over-ride
      redshift_regions = [self.filter_region]

    # iterate
    region_iterator = redshift_regions
    if display_tqdm:
      # add some spaces for aligning the progress bars
      desc = "%s, counting in all regions     "%self.service_description
      desc = "%-50s"%desc
      region_iterator = self.tqdmman(region_iterator, total = len(redshift_regions), desc=desc)

    for region_name in region_iterator:
      if self.regionInclude_ready and self.filter_region is None:
        if region_name not in self.region_include:
          # skip since already failed to use it
          continue

      logger.debug("Region %s"%region_name)
      boto3.setup_default_session(region_name = region_name)

      # boto3 clients
      # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/redshift.html#Redshift.Client.describe_logging_status
      # Update 2019-12-09
      #   Unfolding the iterator can cause a rate limiting error for accounts with more than 200 EC2
      #   as reported by u/moofishies on 2019-11-12
      #   Similar to: https://github.com/boto/botocore/pull/891#issuecomment-303526763
      #   The max_attempts config here is increased from the default 4 to decrease the rate limiting chances
      #   https://github.com/boto/botocore/pull/1260
      #   Note that with each extra retry, an exponential backoff is already implemented inside botocore
      #   More: https://botocore.amazonaws.com/v1/documentation/api/latest/reference/config.html
      from botocore.config import Config
      service_client = boto3.client(self.service_name, config=Config(retries={'max_attempts': 10}))

      # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html#metric
      self.cloudwatch_resource = boto3.resource('cloudwatch')

      # iterate on service resources, eg ec2 instances, redshift clusters
      paginator = service_client.get_paginator(self.paginator_name)
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

        if not self.regionInclude_ready and self.filter_region is None:
          if region_anyClusterFound:
            # only include if found clusters in this region
            self.region_include.append(region_name)

      except botocore.exceptions.ClientError as e:
        # Exception that means "no access to region"
        if e.response['Error']['Code']==self.paginator_exception:
          continue

        # all other exceptions raised
        raise e

    # before exiting, check if a count just completed, and mark region_include as usable
    if not self.regionInclude_ready and self.filter_region is None:
      self.regionInclude_ready = True

      # save to cache
      import simple_cache
      SECONDS_PER_HOUR = 60*60
      simple_cache.save_key(filename=self.cache_filename, key=self.cache_key, value=self.region_include, ttl=SECONDS_PER_HOUR)


  def count(self):
      # method 1
      # ec2_it = self.ec2_resource.instances.all()
      # return len(list(ec2_it))

    if self.n_entry is not None:
      return self.n_entry

    self.n_entry = len(list(self.iterate_core(True)))

    if self.n_entry==0 and len(self.region_include)==0:
      msg_count = "Found no %s"
      logger.info(msg_count%(self.service_description))
    else:
      msg_count = "Found a total of %i %s in %i region(s) (other regions do not hold any %s)"
      logger.info(msg_count%(self.n_entry, self.service_description, len(self.region_include), self.service_name))

    return self.n_entry


  def __iter__(self):
    for rc_describe_entry in self.iterate_core(False):
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

        # None below is a placeholder for ec2_obj in case of ec2
        yield rc_describe_entry, rc_id, rc_created, None




