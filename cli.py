import boto3
import pandas as pd
import requests
from cachecontrol import CacheControl
from cachecontrol.caches.file_cache import FileCache
from tqdm import tqdm
import datetime as dt
from gitRemoteAws.pull_cloudtrail_lookupEvents import GeneralManager as CloudtrailManager
import numpy as np
import os
import json
import pytz

import logging
logger = logging.getLogger('isitfit')
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)
logger.setLevel(logging.DEBUG)


def mergeSeriesOnTimestampRange(df_cpu, df_type):
  """
  Upsamples df_type to df_cpu.
  Example:
    Input
      df_cpu = pd.Series({'time': [1,2,3,4], 'field_1': [5,6,7,8]})
      df_type = pd.Series({'time': [1,3], 'field_2': ['a','b']})
    Returns
      pd.Series({'time': [1,2,3,4], 'field_1': [5,6,7,8], 'field_2': ['a','a','b','b']})
  """
  df_cpu['instanceType'] = None
  # assume df_type is sorted in decreasing EventTime order (very important)
  # NB: since some instances are not present in the cloudtrail (for which we append artificially the "now" type)
  #     Need to traverse the df_type matrix backwards
  for index, row_type in df_type.iterrows():
      # use row_type.name instead of row_type['EventTime']
      # check note above about needing to traverse backwards
      # df_cpu.iloc[np.where(df_cpu.Timestamp >= row_type.name)[0], df_cpu.columns.get_loc('instanceType')] = row_type['instanceType']
      df_cpu.iloc[np.where(df_cpu.Timestamp <= row_type.name)[0], df_cpu.columns.get_loc('instanceType')] = row_type['instanceType']

  # fill na at beginning with back-fill
  # (artifact of cloudwatch having data at days before the creation of the instance)
  df_cpu['instanceType'] = df_cpu['instanceType'].fillna(method='backfill')
  return df_cpu


SECONDS_IN_ONE_DAY = 60*60*24 # 86400  # used for granularity (daily)
N_DAYS=90

class MainManager:
    def __init__(self):
        self.ec2_resource = boto3.resource('ec2')
        self.cloudwatch_resource = boto3.resource('cloudwatch')

        self.cloudtrail_client = boto3.client('cloudtrail')

        dt_now_d=dt.datetime.now().replace(tzinfo=pytz.utc)
        self.StartTime=dt_now_d - dt.timedelta(days=N_DAYS)
        self.EndTime=dt_now_d
        logger.debug("Metrics start..end: %s .. %s"%(self.StartTime, self.EndTime))


    def get_ifi(self):
        # download ec2 catalog: 2 columns: ec2 type, ec2 cost per hour
        self.df_cat = self._ec2_catalog()

        # get cloudtail ec2 type changes for all instances
        self.df_cloudtrail = self._cloudtrail_ec2type_fetch()

        # 0th pass to count
        n_ec2 = len(list(self.ec2_resource.instances.all()))

        # first pass to append ec2 types to cloudtrail based on "now"
        self.df_cloudtrail = self.df_cloudtrail.reset_index()
        for ec2_obj in tqdm(self.ec2_resource.instances.all(), total=n_ec2, desc="First pass, EC2 instance", initial=1):
            self._cloudtrail_ec2type_appendNow(ec2_obj)

        # set index again, and sort decreasing this time (not like git-remote-aws default)
        self.df_cloudtrail = self.df_cloudtrail.set_index(["instanceId", "EventTime"]).sort_index(ascending=False)

        # iterate over all ec2 instances
        sum_capacity = 0
        sum_used = 0
        df_all = []
        for ec2_obj in tqdm(self.ec2_resource.instances.all(), total=n_ec2, desc="Second pass, EC2 instance", initial=1):
            res_capacity, res_used = self._handle_ec2obj(ec2_obj)
            sum_capacity += res_capacity
            sum_used += res_used
            df_all.append({'instance_id': ec2_obj.instance_id, 'capacity': res_capacity, 'used': res_used})
            logger.debug("\n")

        # for debugging
        df_all = pd.DataFrame(df_all)
        logger.debug("\ncapacity/used per instance")
        logger.debug(df_all)
        logger.debug("\n")

        if sum_capacity==0: return 0

        return sum_used/sum_capacity*100


    def _cloudtrail_ec2type_fetch(self):
        # get cloudtail ec2 type changes for all instances
        # FIXME
        cache_fn = '/tmp/isitfit_cloudtrail.shadiakiki1986.csv'
        # cache_fn = '/tmp/isitfit_cloudtrail.autofitcloud.csv'
        if os.path.exists(cache_fn):
            logger.debug("Loading cloudtrail data from cache")
            df = pd.read_csv(cache_fn).set_index(["instanceId", "EventTime"])
            return df

        logger.debug("Downloading cloudtrail data")
        cloudtrail_manager = CloudtrailManager(self.cloudtrail_client)
        df = cloudtrail_manager.ec2_typeChanges()

        # save to cache
        df.to_csv(cache_fn)

        # done
        return df


    def _ec2_catalog(self):
        logger.debug("Downloading ec2 catalog")
        # based on URL = 'http://www.ec2instances.info/instances.json'
        # URL = 's3://...csv'
        URL = 'https://gitlab.com/autofitcloud/www.ec2instances.info-ec2op/raw/master/www.ec2instances.info/t3b_smaller_familyL2.json'

        # cached https://cachecontrol.readthedocs.io/en/latest/
        sess = requests.session()
        cached_sess = CacheControl(sess, cache=FileCache('/tmp/isitfit_ec2info.cache'))
        r = cached_sess.request('get', URL)

        # read catalog, copy from ec2op-cli/ec2op/optimizer/cwDailyMaxMaxCpu
        j = json.dumps(r.json(), indent=4, sort_keys=True)
        df = pd.read_json(j, orient='split')
        df = df[['API Name', 'Linux On Demand cost']]
        df = df.rename(columns={'Linux On Demand cost': 'cost_hourly'})
        # df = df.set_index('API Name') # need to use merge, not index
        return df

    def _cloudwatch_metrics(self, ec2_obj):
        """
        Return a pandas series of CPU utilization, daily max, for 90 days
        """
        metrics_iterator = self.cloudwatch_resource.metrics.filter(
            Namespace='AWS/EC2', 
            MetricName='CPUUtilization', 
            Dimensions=[{'Name': 'InstanceId', 'Value': ec2_obj.instance_id}]
          )
        df_cw1 = []
        for m_i in metrics_iterator:
            json_i = m_i.get_statistics(
              Dimensions=[{'Name': 'InstanceId', 'Value': ec2_obj.instance_id}],
              Period=SECONDS_IN_ONE_DAY,
              Statistics=['Average', 'SampleCount'],
              Unit='Percent',
              StartTime=self.StartTime,
              EndTime=self.EndTime
            )
            # logger.debug(json_i)
            if len(json_i['Datapoints'])==0: continue # skip (no data)

            df_i = pd.DataFrame(json_i['Datapoints'])
            df_i = df_i[['Timestamp', 'SampleCount', 'Average']]
            df_i = df_i.sort_values(['Timestamp'], ascending=True)
            df_cw1.append(df_i)

        #
        if len(df_cw1)==0:
          # raise ValueError("No metrics for %s"%ec2_obj.instance_id)
          return None

        if len(df_cw1) >1:
          raise ValueError(">1 # metrics for %s"%ec2_obj.instance_id)

        # merge
        # df_cw2 = pd.concat(df_cw1, axis=1)

        # done
        # return df_cw2.CPUUtilization
        return df_cw1[0]


    def _cloudtrail_ec2type_appendNow(self, ec2_obj):
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


    def _cloudtrail_ec2type_single(self, ec2_obj):
        # pandas series of number of cpu's available on the machine over time, past 90 days
        # series_type_ts1 = self.cloudtrail_client.get_ec2_type(ec2_obj.instance_id)
        if not ec2_obj.instance_id in self.df_cloudtrail.index:
            return None

        return self.df_cloudtrail.loc[ec2_obj.instance_id]


    def _handle_ec2obj(self, ec2_obj):
        logger.debug("%s, %s"%(ec2_obj.instance_id, ec2_obj.instance_type))

        # pandas series of CPU utilization, daily max, for 90 days
        df_metrics = self._cloudwatch_metrics(ec2_obj)

        # no data
        if df_metrics is None:
          logger.debug("No cloudwatch")
          return 0, 0

        # pandas series of number of cpu's available on the machine over time, past 90 days
        df_type_ts1 = self._cloudtrail_ec2type_single(ec2_obj)
        if df_type_ts1 is None:
          logger.debug("No cloudtrail")
          return 0,0

        # convert type timeseries to the same timeframes as pcpu and n5mn
        #if ec2_obj.instance_id=='i-069a7808addd143c7':
        #  import pdb
        #  pdb.set_trace()
        ec2_df = mergeSeriesOnTimestampRange(df_metrics, df_type_ts1)
        logger.debug("\nafter merge series on timestamp range")
        logger.debug(ec2_df.head())

        # merge with type changes (can't use .merge on timestamps, need to use .concat)
        #ec2_df = df_metrics.merge(df_type_ts2, left_on='Timestamp', right_on='EventTime', how='left')
        # ec2_df = pd.concat([df_metrics, df_type_ts2], axis=1)

        # merge with catalog
        ec2_df = ec2_df.merge(self.df_cat, left_on='instanceType', right_on='API Name', how='left')
        logger.debug("\nafter merge with catalog")
        logger.debug(ec2_df.head())

        # results: 2 numbers: capacity (USD), used (USD)
        ec2_df['nhours'] = np.ceil(ec2_df.SampleCount/12)
        res_capacity = (ec2_df.nhours*ec2_df.cost_hourly).sum()
        res_used     = (ec2_df.nhours*ec2_df.cost_hourly*ec2_df.Average/100).sum()

        logger.debug("res_capacity=%s, res_used=%s"%(res_capacity, res_used))
        return res_capacity, res_used



if __name__=='__main__':
    mm = MainManager()
    ifi = mm.get_ifi()
    logger.info("IFI = %0.2f%%"%ifi)
    logger.info("(IFI >= 70% is well optimized)")
    logger.info("(IFI <= 30% is underused)")
