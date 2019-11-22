import pandas as pd
from tqdm import tqdm
from .pull_cloudtrail_lookupEvents import GeneralManager as GraCloudtrailManager
import os
from ..utils import NoCloudtrailException

import logging
logger = logging.getLogger('isitfit')


def dict2service(ec2_dict):
        if 'InstanceId' in ec2_dict: return 'EC2'
        if 'ClusterIdentifier' in ec2_dict: return 'Redshift'
        import json
        raise Exception("Unknown service found in %s"%json.dumps(ec2_dict))



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
            self._appendNow(ec2_dict, ec2_id)

        # set index again, and sort decreasing this time (not like git-remote-aws default)
        self.df_cloudtrail = self.df_cloudtrail.set_index(["Region", "ServiceName", "ResourceName", "EventTime"]).sort_index(ascending=False)

        # done
        return context_pre


    def _fetch(self):
        # get cloudtrail ec2 type changes for all instances
        logger.debug("Downloading cloudtrail data (from %i regions)"%len(self.region_include))
        df_2 = []
        import boto3
        iter_wrap = self.region_include
        iter_wrap = tqdm(iter_wrap, desc="Cloudtrail events in all regions", total=len(self.region_include))
        for region_name in iter_wrap:
          boto3.setup_default_session(region_name = region_name)
          cloudtrail_manager = GraCloudtrailManager()
          df_1 = cloudtrail_manager.ec2_typeChanges()
          df_1['region'] = region_name
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
            df = pd.read_csv(cache_fn).set_index(["ResourceName", "EventTime"])
            return df

        logger.debug("Downloading cloudtrail data")
        cloudtrail_manager = GraCloudtrailManager(cloudtrail_client)
        df = cloudtrail_manager.ec2_typeChanges()

        # save to cache
        df.to_csv(cache_fn)

        # done
        return df
    """


    def _appendNow(self, ec2_dict, ec2_id):
        # artificially append an entry for "now" with the current type
        # This is useful for instance who have no entries in the cloudtrail
        # so that their type still shows up on merge

        ec2_dict['ServiceName'] = dict2service(ec2_dict)

        size1_key = 'NodeType' if ec2_dict['ServiceName']=='Redshift' else 'InstanceType'
        size2_val = ec2_dict['NumberOfNodes'] if ec2_dict['ServiceName']=='Redshift' else None

        df_new = pd.DataFrame([
              {
                'Region': ec2_dict['Region'],
                'ServiceName': ec2_dict['ServiceName'],
                'ResourceName': ec2_id,
                'EventTime': self.EndTime,
                'ResourceSize1': ec2_dict[size1_key],
                'ResourceSize2': size2_val
              }
            ])

        self.df_cloudtrail = pd.concat([self.df_cloudtrail, df_new], sort=True)


    def single(self, context_ec2):
        ec2_dict = context_ec2['ec2_dict']

        # imply service name
        ec2_dict['ServiceName'] = dict2service(ec2_dict)
        ServiceName = ec2_dict['ServiceName']
        region_name = ec2_dict['Region']

        sub_ct = self.df_cloudtrail

        sub_ct = sub_ct.loc[region_name]
        if sub_ct.shape[0]==0:
          raise NoCloudtrailException("No cloudtrail data #4 for %s"%ec2_id)

        sub_ct = sub_ct.loc[ServiceName]
        if sub_ct.shape[0]==0:
          raise NoCloudtrailException("No cloudtrail data #3 for %s"%ec2_id)

        # continue
        # ec2_obj = context_ec2['ec2_obj']
        ec2_id = context_ec2['ec2_id']

        # pandas series of number of cpu's available on the machine over time, past 90 days
        # series_type_ts1 = self.cloudtrail_client.get_ec2_type(ec2_obj.instance_id)
        if not ec2_id in sub_ct.index:
          raise NoCloudtrailException("No cloudtrail data #1 for %s"%ec2_id)

        df_type_ts1 = sub_ct.loc[ec2_id]
        if df_type_ts1 is None:
          raise NoCloudtrailException("No cloudtrail data #2 for %s"%ec2_id)

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

