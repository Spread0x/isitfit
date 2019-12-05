import pandas as pd
import os
from ..utils import NoCloudtrailException

from isitfit.utils import logger



from isitfit.cost.cloudtrail_iterator import dict2service


class CloudtrailCached:
    def __init__(self, EndTime, cache_man, tqdmman):
        self.EndTime = EndTime
        self.tqdmman = tqdmman
        self.cache_man = cache_man


    def init_data(self, context_pre):
        # parse out of context
        ec2_instances, region_include, n_ec2 = context_pre['ec2_instances'], context_pre['region_include'], context_pre['n_ec2_total']

        # get cloudtail ec2 type changes for all instances
        from isitfit.cost.cloudtrail_iterator import EventAggregatorPostprocessed
        eap = EventAggregatorPostprocessed(region_include, self.tqdmman, self.cache_man, self.EndTime)
        self.df_cloudtrail = eap.get(ec2_instances, n_ec2)

        # done
        return context_pre


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


