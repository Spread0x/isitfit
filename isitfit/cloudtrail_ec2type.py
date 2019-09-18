import pandas as pd
from tqdm import tqdm
from .pull_cloudtrail_lookupEvents import GeneralManager as GraCloudtrailManager
import os


import logging
logger = logging.getLogger('isitfit')



class Manager:
    def __init__(self, cloudtrail_client, EndTime, cache_man):
        self.cloudtrail_client = cloudtrail_client
        self.EndTime = EndTime
        self.cache_man = cache_man

    def init_data(self, ec2_instances, n_ec2):
        # get cloudtail ec2 type changes for all instances
        self.df_cloudtrail = self._fetch_cached()

        # first pass to append ec2 types to cloudtrail based on "now"
        self.df_cloudtrail = self.df_cloudtrail.reset_index()
        for ec2_obj in tqdm(ec2_instances.all(), total=n_ec2, desc="First pass through EC2 instances", initial=1):
            self._appendNow(ec2_obj)

        # set index again, and sort decreasing this time (not like git-remote-aws default)
        self.df_cloudtrail = self.df_cloudtrail.set_index(["instanceId", "EventTime"]).sort_index(ascending=False)


    def _fetch_cached(self):
        # get cloudtrail ec2 type changes for all instances

        # check cache first
        cache_key = "cloudtrail_ec2type._fetch"
        if self.cache_man.isReady():
          df_cache = self.cache_man.get(cache_key)
          if df_cache is not None:
            logger.debug("Found cloudtrail data in redis cache")
            return df_cache

        # if no cache, then download
        df_fresh = self._fetch_core()

        # if caching enabled, store it for later fetching
        # https://stackoverflow.com/a/57986261/4126114
        if self.cache_man.isReady():
          self.cache_man.set(cache_key, df_fresh)

        # done
        return df_fresh


    def _fetch_core(self):
        # get cloudtrail ec2 type changes for all instances
        logger.debug("Downloading cloudtrail data")
        cloudtrail_manager = GraCloudtrailManager(self.cloudtrail_client)
        df = cloudtrail_manager.ec2_typeChanges()
        return df

    """
    # Cached version ... disabled because not sure how to generalize it
    def _fetch(self):
        # get cloudtail ec2 type changes for all instances
        # FIXME
        cache_fn = '/tmp/isitfit_cloudtrail.shadiakiki1986.csv'
        # cache_fn = '/tmp/isitfit_cloudtrail.autofitcloud.csv'
        if os.path.exists(cache_fn):
            logger.debug("Loading cloudtrail data from cache")
            df = pd.read_csv(cache_fn).set_index(["instanceId", "EventTime"])
            return df

        logger.debug("Downloading cloudtrail data")
        cloudtrail_manager = GraCloudtrailManager(self.cloudtrail_client)
        df = cloudtrail_manager.ec2_typeChanges()

        # save to cache
        df.to_csv(cache_fn)

        # done
        return df
    """



    def _appendNow(self, ec2_obj):
        # artificially append an entry for "now" with the current type
        # This is useful for instance who have no entries in the cloudtrail
        # so that their type still shows up on merge
        self.df_cloudtrail = pd.concat([
            self.df_cloudtrail,
            pd.DataFrame([
              { 'instanceId': ec2_obj.instance_id,
                'EventTime': self.EndTime,
                'instanceType': ec2_obj.instance_type
              }
            ])
          ])


    def single(self, ec2_obj):
        # pandas series of number of cpu's available on the machine over time, past 90 days
        # series_type_ts1 = self.cloudtrail_client.get_ec2_type(ec2_obj.instance_id)
        if not ec2_obj.instance_id in self.df_cloudtrail.index:
            return None

        return self.df_cloudtrail.loc[ec2_obj.instance_id]


