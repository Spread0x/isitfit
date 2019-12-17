# boto3 implementation of
# https://gist.github.com/shadiakiki1986/f6e676d1ab5800fcf7899b6a392ab821
# Docs
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudtrail.html#CloudTrail.Client.get_paginator
#
# Requirements: pip3 install boto3 tqdm pandas
# Run: python3 t2.py
#
# Edit 2019-09-13: copied file pull_cloudtrail_lookupEvents.py from git-remote-aws into isitfit so as to avoid confusion in download statistics
#----------------------------------------

# imports
import datetime as dt
from dateutil.relativedelta import relativedelta
import boto3
import json

from isitfit.utils import logger


#------------------------------
# utility to serialize date
#def json_serial(obj):
#    """JSON serializer for objects not serializable by default json code"""
#
#    if isinstance(obj, (dt.datetime, dt.date)):
#        return obj.isoformat()
#    raise TypeError ("Type %s not serializable" % type(obj))


#----------------------------------------
# iterate

# use jmespath like awscli
# https://stackoverflow.com/a/57018780/4126114
# Example
#   >>> mydata
#   {'foo': {'bar': [{'name': 'one'}, {'name': 'two'}]}}
#   >>> jmespath.search('foo.bar[?name==`one`]', mydata)
#   [{'name': 'one'}]
# import jmespath

#----------------------------------------
class EventIterator:
    eventName = None
  
    # get paginator
    def iterate_page(self):
        """
        eventName - eg 'ModifyInstanceAttribute'
        """
        if self.eventName is None:
          raise Exception("Derived class should set class member eventName")

        # arguments to lookup-events command
        # From docs: "Currently the list can contain only one item"
        LookupAttributes=[
        #    {'AttributeKey': 'EventSource', 'AttributeValue': 'ec2.amazonaws.com'},
            {'AttributeKey': 'EventName', 'AttributeValue': self.eventName},
        ]

        # go back x time
        # https://stackoverflow.com/a/38795526/4126114
        # StartTime=dt.datetime.now() - relativedelta(years=1)
        # StartTime=dt.datetime.now() - relativedelta(days=90)
        PaginationConfig={
          'MaxResults': 3000
        }

        # edit 2019-11-20 instead of defining this client in Gra... and passing it through several layers,
        # just define it here
        # Note 2019-12-09 Cloudtrail can return a max of 90 days
        # In this class, the start/end dates are not specified so as to fetch the whole 90 days and cache them
        # Not very efficient, but works ATM. This is not a per EC2/Redshift call
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudtrail.html#CloudTrail.Client.lookup_events
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudtrail.html#CloudTrail.Paginator.LookupEvents
        client = boto3.client('cloudtrail')
        self.region_name = client.meta.region_name
        cp = client.get_paginator(operation_name="lookup_events")
        iterator = cp.paginate(
          LookupAttributes=LookupAttributes, 
          #StartTime=StartTime, 
          PaginationConfig=PaginationConfig
        )
        return iterator


    def iterate_event(self):
      iter_wrap = self.iterate_page()
      # Update 2019-11-22 moved this tqdm to the region level since it's already super fast per event
      #iter_wrap = tqdm(iter_wrap, desc="Cloudtrail events for %s/%s"%(self.region_name, self.eventName))
      for response in iter_wrap:
        #with open('t2.json','w') as fh:
        #  json.dump(response, fh, default=json_serial)

        # print(response.keys())
        for event in response['Events']:
          result = self._handleEvent(event)
          if result is None: continue
          yield result


    def _handleEvent(self, event):
        # raise Exception("Implement by derived classes")
        return event


class RedshiftCreate(EventIterator):
    eventName = "CreateCluster"
 
    def _handleEvent(self, event):
          # logger.debug("Cloudtrail event: %s"%json.dumps(event, default=json_serial))

          if 'Resources' not in event:
            logger.debug("No 'Resources' key in event. Skipping")
            return None # ignore this situation
        
          instanceId = [x for x in event['Resources'] if x['ResourceType']=='AWS::Redshift::Cluster']
          if len(instanceId)==0:
            logger.debug("No AWS redshift clusters in event. Skipping")
            return None # ignore this situation

          # proceed
          instanceId = instanceId[0]

          if 'ResourceName' not in instanceId:
            logger.debug("No ResourceName key in event. Skipping")
            return None # ignore this situation
          
          # proceed
          instanceId = instanceId['ResourceName']

          if 'CloudTrailEvent' not in event:
            logger.debug("No CloudTrailEvent key in event. Skipping")
            return None # ignore this situation

          ce_dict = json.loads(event['CloudTrailEvent'])

          import jmespath
          nodeType = jmespath.search('requestParameters.nodeType', ce_dict)
          numberOfNodes = jmespath.search('requestParameters.numberOfNodes', ce_dict)
          if numberOfNodes is None:
            numberOfNodes = jmespath.search('responseElements.numberOfNodes', ce_dict)

          if nodeType is None:
            logger.debug("No nodeType key in event['CloudTrailEvent']['requestParameters']. Skipping")
            return None # ignore this situation

          if numberOfNodes is None:
            logger.debug("No numberOfNodes key in event['CloudTrailEvent']['requestParameters']. Skipping")
            return None # ignore this situation

          if 'EventTime' not in event:
            logger.debug("No EventTime key in event. Skipping")
            return None # ignore this situation

          ts_obj = event['EventTime']
          # ts_obj = dt.datetime.utcfromtimestamp(ts_int)
          # ts_str = ts_obj.strftime('%Y-%m-%d %H:%M:%S')

          result = {
            'ServiceName': 'Redshift', # bugfix: was using Ec2 instead of Redshift
            'EventName': self.eventName,
            'EventTime': ts_obj,  # ts_str,
            'ResourceName': instanceId,
            'ResourceSize1': nodeType,
            'ResourceSize2': numberOfNodes,
          }

          return result

      
      
class Ec2Run(EventIterator):
    eventName = "RunInstances"
 
    def _handleEvent(self, event):
          # logger.debug("Cloudtrail event: %s"%json.dumps(event, default=json_serial))

          if 'Resources' not in event:
            logger.debug("No 'Resources' key in event. Skipping")
            return None # ignore this situation
        
          instanceId = [x for x in event['Resources'] if x['ResourceType']=='AWS::EC2::Instance']
          if len(instanceId)==0:
            logger.debug("No AWS EC2 instances in event. Skipping")
            return None # ignore this situation

          # proceed
          instanceId = instanceId[0]

          if 'ResourceName' not in instanceId:
            logger.debug("No ResourceName key in event. Skipping")
            return None # ignore this situation
          
          # proceed
          instanceId = instanceId['ResourceName']

          if 'CloudTrailEvent' not in event:
            logger.debug("No CloudTrailEvent key in event. Skipping")
            return None # ignore this situation

          ce_dict = json.loads(event['CloudTrailEvent'])

          if 'requestParameters' not in ce_dict:
            logger.debug("No requestParameters key in event['CloudTrailEvent']. Skipping")
            return None # ignore this situation

          if 'instanceType' not in ce_dict['requestParameters']:
            logger.debug("No instanceType key in event['CloudTrailEvent']['requestParameters']. Skipping")
            return None # ignore this situation

          newType = ce_dict['requestParameters']['instanceType']

          if 'EventTime' not in event:
            logger.debug("No EventTime key in event. Skipping")
            return None # ignore this situation

          ts_obj = event['EventTime']
          # ts_obj = dt.datetime.utcfromtimestamp(ts_int)
          # ts_str = ts_obj.strftime('%Y-%m-%d %H:%M:%S')

          result = {
            'ServiceName': 'EC2',
            'EventName': self.eventName,
            'EventTime': ts_obj,  # ts_str,
            'ResourceName': instanceId,
            'ResourceSize1': newType,
            'ResourceSize2': None
          }

          return result
          
          
class Ec2Modify(EventIterator):
    eventName = "ModifyInstanceAttribute"
 
    def _handleEvent(self, event):
          if 'CloudTrailEvent' not in event:
            logger.debug("No CloudTrailEvent key in event. Skipping")
            return None # ignore this situation

          ce_dict = json.loads(event['CloudTrailEvent'])

          if 'requestParameters' not in ce_dict:
            logger.debug("No requestParameters key in event['CloudTrailEvent']. Skipping")
            return None # ignore this situation

          rp_dict = ce_dict['requestParameters']
          newType = None

          #newType = jmespath.search('instanceType', rp_dict)
          #if newType is None:
          #  newType = jmespath.search('attributeName==`instanceType`', rp_dict)

          if 'instanceType' in rp_dict:
            # logging.error(json.dumps(rp_dict))
            newType = rp_dict['instanceType']['value']

          if 'attribute' in rp_dict:
            if rp_dict['attribute']=='instanceType':
              newType = rp_dict['value']

          if newType is None:
            return None

          ts_obj = event['EventTime']
          # ts_obj = dt.datetime.utcfromtimestamp(ts_int)
          # ts_str = ts_obj.strftime('%Y-%m-%d %H:%M:%S')

          if 'instanceId' not in rp_dict:
            logger.debug("No instanceId key in requestParameters. Skipping")
            return None # ignore this situation

          result = {
            'ServiceName': 'EC2',
            'EventName': self.eventName,
            'EventTime': ts_obj, # ts_str,
            'ResourceName': rp_dict['instanceId'],
            'ResourceSize1': newType,
            'ResourceSize2': None
          }

          return result


class RedshiftResize(EventIterator):
    eventName = "ResizeCluster"
 
    def _handleEvent(self, event):
          if 'CloudTrailEvent' not in event:
            logger.debug("No CloudTrailEvent key in event. Skipping")
            return None # ignore this situation

          ce_dict = json.loads(event['CloudTrailEvent'])

          if 'requestParameters' not in ce_dict:
            logger.debug("No requestParameters key in event['CloudTrailEvent']. Skipping")
            return None # ignore this situation

          rp_dict = ce_dict['requestParameters']

          import jmespath
          nodeType = jmespath.search('instanceType', rp_dict)
          numberOfNodes = jmespath.search('numberOfNodes', rp_dict)

          ts_obj = event['EventTime']
          # ts_obj = dt.datetime.utcfromtimestamp(ts_int)
          # ts_str = ts_obj.strftime('%Y-%m-%d %H:%M:%S')

          result = {
            'ServiceName': 'Redshift',
            'ResourceName': rp_dict['clusterIdentifier'],
            'EventTime': ts_obj, # ts_str,

            'EventName': self.eventName,
            'ResourceSize1': nodeType,
            'ResourceSize2': numberOfNodes,

          }

          return result


import pandas as pd

class EventAggregatorOneRegion:
    def get(self):
        from termcolor import colored
        import botocore
        import sys

        def run_iterator(man2_i):
          try:
            r_i = list(man2_i.iterate_event())
          except botocore.exceptions.ClientError as e:
            # display error message without the frightening traceback
            from isitfit.cli.click_descendents import IsitfitCliError
            raise IsitfitCliError(str(e))

          return r_i

        man2_ec2run = Ec2Run()
        r_ec2run = run_iterator(man2_ec2run)
        
        man2_ec2mod = Ec2Modify()
        r_ec2mod = run_iterator(man2_ec2mod)
       
        man2_rscre = RedshiftCreate()
        r_rscre = run_iterator(man2_rscre)

        man2_rsmod = RedshiftResize()
        r_rsmod = run_iterator(man2_rsmod)

        # split on instance ID and gather
        r_all = r_ec2run + r_ec2mod + r_rscre + r_rsmod
        # logging.error(r_all)
        df = pd.DataFrame(r_all)

        if df.shape[0]==0:
          # early return
          return df

        df = df.set_index(["ServiceName", "ResourceName", "EventTime"]).sort_index()
        
        return df



class EventAggregatorAllRegions(EventAggregatorOneRegion):
    def __init__(self, region_include, tqdmman):
      self.region_include = region_include
      self.tqdmman = tqdmman

    def get(self):
        # get cloudtrail ec2 type changes for all instances
        logger.debug("Downloading cloudtrail data (from %i regions)"%len(self.region_include))
        df_2 = []
        import boto3

        # add some spaces for aligning the progress bars
        desc="Cloudtrail events in all regions"
        desc = "%-50s"%desc

        iter_wrap = self.region_include
        iter_wrap = self.tqdmman(iter_wrap, desc=desc, total=len(self.region_include))
        for region_name in iter_wrap:
          boto3.setup_default_session(region_name = region_name)
          df_1 = super().get()
          df_1['Region'] = region_name # bugfix, field name was "region" (lower-case)
          df_2.append(df_1.reset_index())

        # concatenate
        df_3 = pd.concat(df_2, axis=0, sort=False)

        # check if empty
        if df_3.shape[0]==0:
          return df_3

        # sort again
        df_3 = df_3.set_index(["Region", "ServiceName", "ResourceName", "EventTime"]).sort_index()

        return df_3




class EventAggregatorCached(EventAggregatorAllRegions):
    cache_key = "cloudtrail_ec2type._fetch"

    def __init__(self, region_include, tqdmman, cache_man):
        super().__init__(region_include, tqdmman)
        self.cache_man = cache_man


    def get(self):
        # get cloudtrail ec2 type changes for all instances

        # if not configured, just return
        if self.cache_man is None:
          df_fresh = super().get()
          return df_fresh

        # check cache first
        if self.cache_man.isReady():
          df_cache = self.cache_man.get(self.cache_key)
          if df_cache is not None:
            logger.debug("Found cloudtrail data in redis cache")
            return df_cache

        # if no cache, then download
        df_fresh = super().get()

        # if caching enabled, store it for later fetching
        # https://stackoverflow.com/a/57986261/4126114
        if self.cache_man.isReady():
          self.cache_man.set(self.cache_key, df_fresh)

        # done
        return df_fresh





def dict2service(ec2_dict):
        if 'InstanceId' in ec2_dict: return 'EC2'
        if 'ClusterIdentifier' in ec2_dict: return 'Redshift'
        import json
        raise Exception("Unknown service found in %s"%json.dumps(ec2_dict))



class EventAggregatorPostprocessed(EventAggregatorCached):
    def __init__(self, region_include, tqdmman, cache_man, EndTime):
        super().__init__(region_include, tqdmman, cache_man)
        self.EndTime = EndTime


    def get(self, ec2_instances, n_ec2):
        self.df_cloudtrail = super().get()

        # first pass to append ec2 types to cloudtrail based on "now"
        self.df_cloudtrail = self.df_cloudtrail.reset_index()

        # add some spaces for aligning the progress bars
        desc = "Pass 1/2 Cloudtrail history (EC2, Redshift)"
        desc = "%-50s"%desc

        # Edit 2019-11-12 use initial=0 otherwise if "=1" used then the tqdm output would be "101it" at conclusion, i.e.
        # First pass through EC2 instances: 101it [00:05,  5.19it/s]
        t_iter = ec2_instances
        t_iter = self.tqdmman(t_iter, total=n_ec2, desc=desc, initial=0)
        for ec2_dict, ec2_id, ec2_launchtime, ec2_obj in t_iter:
            self._appendNow(ec2_dict, ec2_id)

        # if still no data, just return
        if self.df_cloudtrail.shape[0]==0:
          return self.df_cloudtrail

        # set index again, and sort decreasing this time (not like git-remote-aws default)
        # The descending sort is very important for the mergeTimeseries... function
        self.df_cloudtrail = self.df_cloudtrail.set_index(["Region", "ServiceName", "ResourceName", "EventTime"]).sort_index(ascending=False)

        # done
        return self.df_cloudtrail


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

