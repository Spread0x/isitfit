import boto3
import pandas as pd
import datetime as dt
import pytz

from isitfit.utils import logger

from ..utils import SECONDS_IN_ONE_DAY, myreturn, NoCloudtrailException, IsitfitCliRunnerBreakIterator

MINUTES_IN_ONE_DAY = 60*24 # 1440


from isitfit.cost.cacheManager import RedisPandas as RedisPandasCacheManager
class EventBus:
    """
    Event bus design pattern
    https://dzone.com/articles/design-patterns-event-bus
    3 event types: pre, ec2, all
    pre: event that is triggered before iterating on the resources
    ec2: event that is triggered for each resource
    all: event that is triggered after iterating on the resources

    The pre event is triggered for all listeners before iterating on the resources.
    The all event is triggered for all listeners after iterating on the resources
    The ec2 event is triggered for all listeners for each resource

    In the dzone.com jargon, listener = subscribable

    This loose coupling allows for parallelization at a later stage
    """
    def __init__(self, description, ctx):
        # description to keep track of each pipeline runner
        self.description = description
        self.set_ndays(90) # default is 90 days

        # listeners post ec2 data fetch and post all activities
        self.listeners = {'pre':[], 'ec2': [], 'all': []}

        # click context for errors
        self.ctx = ctx


    def set_ndays(self, ndays):
        self.ndays = ndays

        # set start/end dates
        dt_now_d=dt.datetime.now().replace(tzinfo=pytz.utc)
        self.StartTime=dt_now_d - dt.timedelta(days=self.ndays)
        self.EndTime=dt_now_d
        logger.debug("Metrics start..end: %s .. %s"%(self.StartTime, self.EndTime))


    def set_iterator(self, ec2_it):
        # generic iterator (iterates over regions and items)
        self.ec2_it = ec2_it


    def add_listener(self, event, listener):
      if event not in self.listeners:
        from isitfit.cli.click_descendents import IsitfitCliError
        err_msg = "Internal dev error: Event %s is not supported for listeners. Use: %s"%(event, ",".join(self.listeners.keys()))
        raise IsitfitCliError(err_msg, self.ctx)

      self.listeners[event].append(listener)


    def get_ifi(self, tqdml2_obj):
      raise Exception("Define in derived class")



class MainManager(EventBus):

    def get_ifi(self, tqdml2_obj):
        # display name of runner
        logger.info(self.description)

        # 0th pass to count
        n_ec2_total = self.ec2_it.count()

        if n_ec2_total==0:
          import click
          click.secho("No resources found in %s"%self.ec2_it.service_description, fg="red")
          return

        # context for pre listeners
        context_pre = {}
        context_pre['ec2_instances'] = self.ec2_it
        context_pre['region_include'] = self.ec2_it.get_regionInclude()
        context_pre['n_ec2_total'] = n_ec2_total
        context_pre['click_ctx'] = self.ctx
        context_pre['mainManager'] = self

        # call listeners
        for l in self.listeners['pre']:
          context_pre = l(context_pre)
          if context_pre is None:
            raise Exception("Breaking the chain is not allowed in listener/pre")

        # iterate over all ec2 instances
        sum_capacity = 0
        sum_used = 0
        df_all = []
        ec2_noCloudwatch = [] # FIXME DEPRECATED
        ec2_noCloudtrail = []

        # add some spaces for aligning the progress bars
        desc="Pass 2/2 through %s"%self.ec2_it.service_description
        desc = "%-50s"%desc

        # Edit 2019-11-12 use "initial=0" instead of "=1". Check more details in a similar note in "cloudtrail_ec2type.py"
        iter_wrap = tqdml2_obj(self.ec2_it, total=n_ec2_total, desc=desc, initial=0)
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

              # skip rest of listeners if one of them returned None
              if context_ec2 is None:
                logger.debug("Listener %s is breaking per_resource for resource %s"%(l, ec2_id))
                break

          except NoCloudtrailException:
            ec2_noCloudtrail.append(ec2_id)

          except IsitfitCliRunnerBreakIterator as e:
            # check request for breaking from the iterator loop
            # eg for isitfit cost optimize --n=1
            logger.debug("Breaking from the per-resource iterator")
            break


        # call listeners
        #logger.info("... done")
        #logger.info("")
        #logger.info("")

        # set up context
        context_all = {}
        context_all['n_ec2_total'] = n_ec2_total
        context_all['mainManager'] = self
        context_all['region_include'] = self.ec2_it.region_include
        if 'df_cat' in context_pre: context_all['df_cat'] = context_pre['df_cat'] # copy object between contexts

        # more
        context_all['ec2_noCloudwatch'] = ec2_noCloudwatch # FIXME DEPRECATED
        context_all['ec2_noCloudtrail'] = ec2_noCloudtrail
        context_all['click_ctx'] = self.ctx

        # call listeners
        for l in self.listeners['all']:
          context_all = l(context_all)
          if context_all is None:
            raise Exception("Breaking the chain is not allowed in listener/all: %s"%str(l))

        # done
        #logger.info("")
        return context_all



class RunnerAccount(EventBus):
  def get_ifi(self, tqdml2_obj):
    if len(self.listeners['pre']) > 0:
        context_pre = {}
        # call listeners
        for l in self.listeners['pre']:
          context_pre = l(context_pre)
          if context_pre is None:
            raise Exception("Breaking the chain is not allowed in listener/pre")

    if len(self.listeners['ec2']) > 0:
        # iterate over services
        n_service_total = self.ec2_it.count()
        iter_wrap = tqdml2_obj(self.ec2_it, total=n_service_total, desc=self.ec2_it.service_description, initial=0)
        for ec2_dict, ec2_id, ec2_launchtime, ec2_obj in iter_wrap:

          # context dict to be passed between listeners
          context_ec2 = {}
          context_ec2['ec2_id'] = ec2_id
          context_ec2['ec2_obj'] = ec2_obj

          # call listeners
          # Listener can return None to break out of loop,
          # i.e. to stop processing with other listeners
          for l in self.listeners['ec2']:
            context_ec2 = l(context_ec2)

            # skip rest of listeners if one of them returned None
            if context_ec2 is None: break

    if len(self.listeners['all']) > 0:
        # set up context
        context_all = {}
        context_all['click_ctx'] = self.ctx

        # call listeners
        for l in self.listeners['all']:
          context_all = l(context_all)
          if context_all is None:
            raise Exception("Breaking the chain is not allowed in listener/all: %s"%str(l))

