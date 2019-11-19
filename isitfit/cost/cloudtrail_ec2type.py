import pandas as pd
from tqdm import tqdm
from .pull_cloudtrail_lookupEvents import GeneralManager as GraCloudtrailManager
import os
from ..utils import NoCloudtrailException

import logging
logger = logging.getLogger('isitfit')



class Manager:
    def __init__(self, EndTime):
        self.EndTime = EndTime

    def init_data(self, context_pre):
        # parse out of context
        ec2_instances, region_include, n_ec2 = context_pre['ec2_instances'], context_pre['region_include'], context_pre['n_ec2_total']

        # get cloudtail ec2 type changes for all instances
        self.region_include = region_include
        self.df_cloudtrail = self._fetch()

        # first pass to append ec2 types to cloudtrail based on "now"
        self.df_cloudtrail = self.df_cloudtrail.reset_index()
        # Edit 2019-11-12 use initial=0 otherwise if "=1" used then the tqdm output would be "101it" at conclusion, i.e.
        # First pass through EC2 instances: 101it [00:05,  5.19it/s]
        for ec2_dict, ec2_id, ec2_launchtime, ec2_obj in tqdm(ec2_instances, total=n_ec2, desc="Pass 1/2 through EC2 instances", initial=0):
            self._appendNow(ec2_obj)

        # set index again, and sort decreasing this time (not like git-remote-aws default)
        self.df_cloudtrail = self.df_cloudtrail.set_index(["instanceId", "EventTime"]).sort_index(ascending=False)

        # done
        return context_pre


    def _fetch(self):
        # get cloudtrail ec2 type changes for all instances
        logger.debug("Downloading cloudtrail data (from %i regions)"%len(self.region_include))
        df_2 = []
        import boto3
        cloudtrail_client_all = {}
        for region_name in self.region_include:
          if region_name not in cloudtrail_client_all.keys():
            boto3.setup_default_session(region_name = region_name)
            cloudtrail_client_all[region_name] = boto3.client('cloudtrail')

          cloudtrail_client_single = cloudtrail_client_all[region_name]
          cloudtrail_manager = GraCloudtrailManager(cloudtrail_client_single)
          df_1 = cloudtrail_manager.ec2_typeChanges()
          df_2.append(df_1)

        # concatenate
        df_3 = pd.concat(df_2, axis=0)
        return df_3

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
        cloudtrail_manager = GraCloudtrailManager(cloudtrail_client)
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
        df_new = pd.DataFrame([
              { 'instanceId': ec2_obj.instance_id,
                'EventTime': self.EndTime,
                'instanceType': ec2_obj.instance_type
              }
            ])

        self.df_cloudtrail = pd.concat([self.df_cloudtrail, df_new], sort=True)


    def single(self, context_ec2):
        ec2_obj = context_ec2['ec2_obj']

        # pandas series of number of cpu's available on the machine over time, past 90 days
        # series_type_ts1 = self.cloudtrail_client.get_ec2_type(ec2_obj.instance_id)
        if not ec2_obj.instance_id in self.df_cloudtrail.index:
            return None

        df_type_ts1 = self.df_cloudtrail.loc[ec2_obj.instance_id]
        if df_type_ts1 is None:
          raise NoCloudtrailException("No cloudtrail data for %s"%ec2_obj.instance_id)

        # set in context
        context_ec2['df_type_ts1'] = df_type_ts1

        # done
        return context_ec2


class CloudtrailCached(Manager):
    def __init__(self, EndTime, cache_man):
        super().__init__(EndTime)
        self.cache_man = cache_man


    def _fetch(self):
        # get cloudtrail ec2 type changes for all instances

        # check cache first
        cache_key = "cloudtrail_ec2type._fetch"
        if self.cache_man.isReady():
          df_cache = self.cache_man.get(cache_key)
          if df_cache is not None:
            logger.debug("Found cloudtrail data in redis cache")
            return df_cache

        # if no cache, then download
        df_fresh = super()._fetch()

        # if caching enabled, store it for later fetching
        # https://stackoverflow.com/a/57986261/4126114
        if self.cache_man.isReady():
          self.cache_man.set(cache_key, df_fresh)

        # done
        return df_fresh

