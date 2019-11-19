import boto3
import pandas as pd
from tqdm import tqdm
import datetime as dt
import numpy as np
import pytz

import logging
logger = logging.getLogger('isitfit')


from ..utils import mergeSeriesOnTimestampRange, ec2_catalog, SECONDS_IN_ONE_DAY, NoCloudwatchException, myreturn, NoCloudtrailException

MINUTES_IN_ONE_DAY = 60*24 # 1440
N_DAYS=90




from isitfit.cost.cacheManager import RedisPandas as RedisPandasCacheManager
class MainManager:
    def __init__(self, ctx, cache_man=None):
        # set start/end dates
        dt_now_d=dt.datetime.now().replace(tzinfo=pytz.utc)
        self.StartTime=dt_now_d - dt.timedelta(days=N_DAYS)
        self.EndTime=dt_now_d
        logger.debug("Metrics start..end: %s .. %s"%(self.StartTime, self.EndTime))

        # manager of redis-pandas caching
        self.cache_man = cache_man

        # listeners post ec2 data fetch and post all activities
        self.listeners = {'pre':[], 'ec2': [], 'all': []}

        # click context for errors
        self.ctx = ctx

        # generic iterator (iterates over regions and items)
        from isitfit.cost.redshift.iterator import Ec2Iterator
        self.ec2_it = Ec2Iterator()


    def add_listener(self, event, listener):
      if event not in self.listeners:
        from ..utils import IsitfitCliError
        err_msg = "Internal dev error: Event %s is not supported for listeners. Use: %s"%(event, ",".join(self.listeners.keys()))
        raise IsitfitCliError(err_msg, self.ctx)

      self.listeners[event].append(listener)


    def ec2_count(self):
      # method 1
      # ec2_it = self.ec2_resource.instances.all()
      # return len(list(ec2_it))

      # method 2, using the generic iterator
      nc = len(list(self.ec2_it.iterate_core(True, True)))
      msg_count = "Found a total of %i EC2 instance(s) in %i region(s) (other regions do not hold any EC2)"
      logger.warning(msg_count%(nc, len(self.ec2_it.region_include)))
      return nc


    def ec2_iterator(self):
      # method 1
      # ec2_it = self.ec2_resource.instances.all()
      # return ec2_it

      # boto3 ec2 and cloudwatch data
      ec2_resource_all = {}

      # TODO cannot use directly use the iterator exposed in "ec2_it"
      # because it would return the dataframes from Cloudwatch,
      # whereas in the cloudwatch data fetch here, the data gets cached to redis.
      # Once the redshift.iterator can cache to redis, then the cloudwatch part here
      # can also be dropped, as well as using the "ec2_it" iterator directly
      # for ec2_dict in self.ec2_it:
      for ec2_dict in self.ec2_it.iterate_core(True, False):
        if ec2_dict['Region'] not in ec2_resource_all.keys():
          boto3.setup_default_session(region_name = ec2_dict['Region'])
          ec2_resource_all[ec2_dict['Region']] = boto3.resource('ec2')

        ec2_resource_single = ec2_resource_all[ec2_dict['Region']]
        ec2_l = ec2_resource_single.instances.filter(InstanceIds=[ec2_dict['InstanceId']])
        ec2_l = list(ec2_l)
        if len(ec2_l)==0:
          continue # not found

        # yield first entry
        ec2_obj = ec2_l[0]
        ec2_obj.region_name = ec2_dict['Region']
        yield ec2_obj


    def get_ifi(self):
        # 0th pass to count
        n_ec2_total = self.ec2_count()

        if n_ec2_total==0:
          return

        # context for pre listeners
        context_pre = {}
        context_pre['ec2_instances'] = self.ec2_iterator()
        context_pre['region_include'] = self.ec2_it.region_include
        context_pre['n_ec2_total'] = n_ec2_total
        context_pre['click_ctx'] = self.ctx


        # call listeners
        for l in self.listeners['pre']:
          context_pre = l(context_pre)
          if context_pre is None: break

        # download ec2 catalog: 2 columns: ec2 type, ec2 cost per hour
        self.df_cat = ec2_catalog()

        # iterate over all ec2 instances
        n_ec2_analysed = 0
        sum_capacity = 0
        sum_used = 0
        df_all = []
        ec2_noCloudwatch = []
        ec2_noCloudtrail = []
        # Edit 2019-11-12 use "initial=0" instead of "=1". Check more details in a similar note in "cloudtrail_ec2type.py"
        for ec2_obj in tqdm(self.ec2_iterator(), total=n_ec2_total, desc="Pass 2/2 through EC2 instances", initial=0):

          try:
            # context dict to be passed between listeners
            context_ec2 = {}
            context_ec2['ec2_obj'] = ec2_obj
            context_ec2['mainManager'] = self

            n_ec2_analysed += 1

            # call listeners
            # Listener can return None to break out of loop,
            # i.e. to stop processing with other listeners
            for l in self.listeners['ec2']:
              context_ec2 = l(context_ec2)
              if context_ec2 is None: break

          except NoCloudwatchException:
            ec2_noCloudwatch.append(ec2_obj.instance_id)
          except NoCloudtrailException:
            ec2_noCloudtrail.append(ec2_obj.instance_id)

        # call listeners
        logger.info("... done")
        logger.info("")
        logger.info("")

        # get now + 10 minutes
        # http://stackoverflow.com/questions/6205442/ddg#6205529
        dt_now = dt.datetime.now()
        TRY_IN = 10
        now_plus_10 = dt_now + dt.timedelta(minutes = TRY_IN)
        now_plus_10 = now_plus_10.strftime("%H:%M")

        if len(ec2_noCloudwatch)>0:
          n_no_cw = len(ec2_noCloudwatch)
          has_more_cw = "..." if n_no_cw>5 else ""
          l_no_cw = ", ".join(ec2_noCloudwatch[:5])
          logger.warning("No cloudwatch data for %i instances: %s%s"%(n_no_cw, l_no_cw, has_more_cw))
          logger.warning("Try again in %i minutes (at %s) to check for new data"%(TRY_IN, now_plus_10))
          logger.info("")

        if len(ec2_noCloudtrail)>0:
          n_no_ct = len(ec2_noCloudtrail)
          has_more_ct = "..." if n_no_ct>5 else ""
          l_no_ct = ", ".join(ec2_noCloudtrail[:5])
          logger.warning("No cloudtrail data for %i instances: %s%s"%(n_no_ct, l_no_ct, has_more_ct))
          logger.warning("Try again in %i minutes (at %s) to check for new data"%(TRY_IN, now_plus_10))
          logger.info("")

        for l in self.listeners['all']:
          l(n_ec2_total, self, n_ec2_analysed, self.ec2_it.region_include)

        logger.info("")
        logger.info("")
        return


    def _handle_ec2obj(self, context_ec2):
        # parse out
        ec2_obj = context_ec2['ec2_obj']

        # logger.debug("%s, %s"%(ec2_obj.instance_id, ec2_obj.instance_type))

        # pandas series of CPU utilization, daily max, for 90 days
        df_metrics = context_ec2['df_metrics']

        # pandas series of number of cpu's available on the machine over time, past 90 days
        df_type_ts1 = context_ec2['df_type_ts1']

        # this is redundant with the implementation in _cloudwatch_metrics_core,
        # and it's here just in case the cached redis version is not a date,
        # but it's not really worth it to make a full refresh of the cache for this
        # if df_metrics.Timestamp.dtype==dt.date:
        try:
          df_metrics['Timestamp'] = df_metrics.Timestamp.dt.date
        except AttributeError:
          pass

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

        # set in context
        context_ec2['ec2_df'] = ec2_df

        # done
        return context_ec2
