import boto3
import pandas as pd
from tqdm import tqdm
import datetime as dt
import pytz

import logging
logger = logging.getLogger('isitfit')


from ..utils import SECONDS_IN_ONE_DAY, NoCloudwatchException, myreturn, NoCloudtrailException

MINUTES_IN_ONE_DAY = 60*24 # 1440
N_DAYS=90




from isitfit.cost.cacheManager import RedisPandas as RedisPandasCacheManager
class MainManager:
    def __init__(self, ctx):
        # set start/end dates
        dt_now_d=dt.datetime.now().replace(tzinfo=pytz.utc)
        self.StartTime=dt_now_d - dt.timedelta(days=N_DAYS)
        self.EndTime=dt_now_d
        logger.debug("Metrics start..end: %s .. %s"%(self.StartTime, self.EndTime))

        # listeners post ec2 data fetch and post all activities
        self.listeners = {'pre':[], 'ec2': [], 'all': []}

        # click context for errors
        self.ctx = ctx


    def set_iterator(self, ec2_it):
        # generic iterator (iterates over regions and items)
        self.ec2_it = ec2_it


    def add_listener(self, event, listener):
      if event not in self.listeners:
        from ..utils import IsitfitCliError
        err_msg = "Internal dev error: Event %s is not supported for listeners. Use: %s"%(event, ",".join(self.listeners.keys()))
        raise IsitfitCliError(err_msg, self.ctx)

      self.listeners[event].append(listener)


    def get_ifi(self):
        # 0th pass to count
        n_ec2_total = self.ec2_it.count()

        if n_ec2_total==0:
          return

        # context for pre listeners
        context_pre = {}
        context_pre['ec2_instances'] = self.ec2_it
        context_pre['region_include'] = self.ec2_it.get_regionInclude()
        context_pre['n_ec2_total'] = n_ec2_total
        context_pre['click_ctx'] = self.ctx


        # call listeners
        for l in self.listeners['pre']:
          context_pre = l(context_pre)
          if context_pre is None:
            raise Exception("Breaking the chain is not allowed in listener/pre")


        # iterate over all ec2 instances
        sum_capacity = 0
        sum_used = 0
        df_all = []
        ec2_noCloudwatch = []
        ec2_noCloudtrail = []

        # Edit 2019-11-12 use "initial=0" instead of "=1". Check more details in a similar note in "cloudtrail_ec2type.py"
        iter_wrap = tqdm(self.ec2_it, total=n_ec2_total, desc="Pass 2/2 through %s"%self.ec2_it.service_description, initial=0)
        for ec2_dict, ec2_id, ec2_launchtime, ec2_obj in iter_wrap:

          # context dict to be passed between listeners
          context_ec2 = {}
          context_ec2['mainManager'] = self
          if 'df_cat' in context_pre: context_ec2['df_cat'] = context_pre['df_cat'] # copy object between contexts
          context_ec2['ec2_dict'] = ec2_dict
          context_ec2['ec2_id'] = ec2_id
          context_ec2['ec2_launchtime'] = ec2_launchtime
          context_ec2['ec2_obj'] = ec2_obj

          try:
            # call listeners
            # Listener can return None to break out of loop,
            # i.e. to stop processing with other listeners
            for l in self.listeners['ec2']:
              context_ec2 = l(context_ec2)
              if context_ec2 is None: break

          except NoCloudwatchException:
            ec2_noCloudwatch.append(ec2_id)
          except NoCloudtrailException:
            ec2_noCloudtrail.append(ec2_id)

          # check special keyword for breaking from the iterator loop
          # eg for isitfit cost optimize --n=1
          if context_ec2 is not None:
            if "break_iterator" in context_ec2:
              if context_ec2["break_iterator"]:
                break

        # call listeners
        logger.info("... done")
        logger.info("")
        logger.info("")

        # set up context
        context_all = {}
        context_all['n_ec2_total'] = n_ec2_total
        context_all['mainManager'] = self
        context_all['region_include'] = self.ec2_it.region_include
        if 'df_cat' in context_pre: context_all['df_cat'] = context_pre['df_cat'] # copy object between contexts

        # more
        context_all['ec2_noCloudwatch'] = ec2_noCloudwatch
        context_all['ec2_noCloudtrail'] = ec2_noCloudtrail
        context_all['click_ctx'] = self.ctx

        # call listeners
        for l in self.listeners['all']:
          context_all = l(context_all)
          if context_all is None:
            raise Exception("Breaking the chain is not allowed in listener/all: %s"%str(l))

        logger.info("")
        logger.info("")
        return


