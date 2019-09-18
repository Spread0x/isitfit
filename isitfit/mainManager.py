import boto3
import pandas as pd
from tqdm import tqdm
import datetime as dt
import numpy as np
import pytz
from .cacheManager import RedisPandas as RedisPandasCacheManager

import logging
logger = logging.getLogger('isitfit')


from .utils import mergeSeriesOnTimestampRange, ec2_catalog
from .cloudtrail_ec2type import Manager as CloudtrailEc2typeManager


SECONDS_IN_ONE_DAY = 60*60*24 # 86400  # used for granularity (daily)
MINUTES_IN_ONE_DAY = 60*24 # 1440
N_DAYS=90


class NoCloudtrailException(Exception):
    pass

class NoCloudwatchException(Exception):
    pass


class MainManager:
    def __init__(self):
        # boto3 ec2 and cloudwatch data
        self.ec2_resource = boto3.resource('ec2')
        self.cloudwatch_resource = boto3.resource('cloudwatch')

        # set start/end dates
        dt_now_d=dt.datetime.now().replace(tzinfo=pytz.utc)
        self.StartTime=dt_now_d - dt.timedelta(days=N_DAYS)
        self.EndTime=dt_now_d
        logger.debug("Metrics start..end: %s .. %s"%(self.StartTime, self.EndTime))

        # manager of redis-pandas caching
        self.cache_man = RedisPandasCacheManager()

        # boto3 cloudtrail data
        cloudtrail_client = boto3.client('cloudtrail')
        self.cloudtrail_manager = CloudtrailEc2typeManager(cloudtrail_client, dt_now_d, self.cache_man)

        # listeners post ec2 data fetch and post all activities
        self.listeners = {'ec2': [], 'all': []}



    def add_listener(self, event, listener):
      if event not in self.listeners:
        raise ValueError("Event %s is not supported for listeners. Use: %s"%(event, ",".join(self.listeners.keys())))

      self.listeners[event].append(listener)


    def get_ifi(self):
        # set up caching if requested
        self.cache_man.fetch_envvars()
        if self.cache_man.isSetup():
          self.cache_man.connect()

        # 0th pass to count
        n_ec2 = len(list(self.ec2_resource.instances.all()))
        logger.warning("Found %i EC2 instances"%n_ec2)

        if n_ec2==0:
          return

        # download ec2 catalog: 2 columns: ec2 type, ec2 cost per hour
        self.df_cat = ec2_catalog()

        # get cloudtail ec2 type changes for all instances
        self.cloudtrail_manager.init_data(self.ec2_resource.instances.all(), n_ec2)

        # iterate over all ec2 instances
        sum_capacity = 0
        sum_used = 0
        df_all = []
        ec2_noCloudwatch = []
        ec2_noCloudtrail = []
        for ec2_obj in tqdm(self.ec2_resource.instances.all(), total=n_ec2, desc="Second pass through EC2 instances", initial=1):
          try:
            self._handle_ec2obj(ec2_obj)
          except NoCloudwatchException:
            ec2_noCloudwatch.append(ec2_obj.instance_id)
          except NoCloudtrailException:
            ec2_noCloudtrail.append(ec2_obj.instance_id)

        # call listeners
        logger.info("... done")
        logger.info("")
        logger.info("")

        if len(ec2_noCloudwatch)>0:
          logger.warning("No cloudwatch data for: %s"%", ".join(ec2_noCloudwatch))
          logger.info("")

        if len(ec2_noCloudtrail)>0:
          logger.warning("No cloudtrail data for: %s"%", ".join(ec2_noCloudtrail))
          logger.info("")

        for l in self.listeners['all']:
          l(n_ec2, self)

        logger.info("")
        logger.info("")
        return


    def _cloudwatch_metrics_cached(self, ec2_obj):
        # check cache first
        cache_key = "mainManager._cloudwatch_metrics/%s"%ec2_obj.instance_id
        if self.cache_man.isReady():
          df_cache = self.cache_man.get(cache_key)
          if df_cache is not None:
            logger.debug("Found cloudwatch metrics in redis cache for %s"%ec2_obj.instance_id)
            return df_cache

        # if no cache, then download
        df_fresh = self._cloudwatch_metrics_core(ec2_obj)

        # if caching enabled, store it for later fetching
        # https://stackoverflow.com/a/57986261/4126114
        # Note that this even stores the result if it was "None" (meaning that no data was found)
        if self.cache_man.isReady():
          self.cache_man.set(cache_key, df_fresh)

        # done
        return df_fresh


    def _cloudwatch_metrics_core(self, ec2_obj):
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
              Statistics=['Average', 'SampleCount', 'Maximum'],
              Unit='Percent',
              StartTime=self.StartTime,
              EndTime=self.EndTime
            )
            # logger.debug(json_i)
            if len(json_i['Datapoints'])==0: continue # skip (no data)

            df_i = pd.DataFrame(json_i['Datapoints'])

            # edit 2019-09-13: no need to subsample columns
            # The initial goal was to drop the "Unit" column (which just said "Percent"),
            # but it's not such a big deal, and avoiding this subsampling simplifies the code a bit
            # df_i = df_i[['Timestamp', 'SampleCount', 'Average']]

            # sort and append in case of multiple metrics
            df_i = df_i.sort_values(['Timestamp'], ascending=True)
            df_cw1.append(df_i)

        if len(df_cw1)==0:
          return None

        if len(df_cw1) >1:
          raise ValueError("More than 1 cloudwatch metric found for %s"%ec2_obj.instance_id)

        # merge
        # df_cw2 = pd.concat(df_cw1, axis=1)

        # dataframe to be returned
        df_cw3 = df_cw1[0]

        # before returning, convert dateutil timezone to pytz
        # for https://github.com/pandas-dev/pandas/issues/25423
        # via https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.Series.dt.tz_convert.html
        df_cw3['Timestamp'] = df_cw3.Timestamp.dt.tz_convert(pytz.utc)

        # done
        return df_cw3


    def _handle_ec2obj(self, ec2_obj):
        # logger.debug("%s, %s"%(ec2_obj.instance_id, ec2_obj.instance_type))

        # pandas series of CPU utilization, daily max, for 90 days
        df_metrics = self._cloudwatch_metrics_cached(ec2_obj)

        # no data
        if df_metrics is None:
          raise NoCloudwatchException("No cloudwatch data for %s"%ec2_obj.instance_id)

        # pandas series of number of cpu's available on the machine over time, past 90 days
        df_type_ts1 = self.cloudtrail_manager.single(ec2_obj)
        if df_type_ts1 is None:
          raise NoCloudtrailException("No cloudtrail data for %s"%ec2_obj.instance_id)

        # convert type timeseries to the same timeframes as pcpu and n5mn
        #if ec2_obj.instance_id=='i-069a7808addd143c7':
        ec2_df = mergeSeriesOnTimestampRange(df_metrics, df_type_ts1)
        #logger.debug("\nafter merge series on timestamp range")
        #logger.debug(ec2_df.head())

        # merge with type changes (can't use .merge on timestamps, need to use .concat)
        #ec2_df = df_metrics.merge(df_type_ts2, left_on='Timestamp', right_on='EventTime', how='left')
        # ec2_df = pd.concat([df_metrics, df_type_ts2], axis=1)

        # merge with catalog
        ec2_df = ec2_df.merge(self.df_cat[['API Name', 'cost_hourly']], left_on='instanceType', right_on='API Name', how='left')
        #logger.debug("\nafter merge with catalog")
        #logger.debug(ec2_df.head())

        # calculate number of running hours
        # In the latest 90 days, sampling is per minute in cloudwatch
        # https://aws.amazon.com/cloudwatch/faqs/
        # Q: What is the minimum resolution for the data that Amazon CloudWatch receives and aggregates?
        # A: ... For example, if you request for 1-minute data for a day from 10 days ago, you will receive the 1440 data points ...
        ec2_df['nhours'] = np.ceil(ec2_df.SampleCount/60)

        # call listeners
        for l in self.listeners['ec2']:
          l(ec2_obj, ec2_df)

        return 0
