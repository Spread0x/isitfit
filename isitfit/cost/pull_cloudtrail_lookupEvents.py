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
from tqdm import tqdm
import json

import logging
logger = logging.getLogger('isitfit')

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
class Ec2TypechangesBase:
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


class RedshiftTypechangesCreate(Ec2TypechangesBase):
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
            'ServiceName': 'EC2',
            'EventName': self.eventName,
            'EventTime': ts_obj,  # ts_str,
            'ResourceName': instanceId,
            'ResourceSize1': nodeType,
            'ResourceSize2': numberOfNodes,
          }

          return result

      
      
class Ec2TypechangesRun(Ec2TypechangesBase):
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
            'EventTime': ts_obj,  # ts_str,
            'ResourceName': instanceId,
            'ResourceSize1': newType,
          }

          return result
          
          
class Ec2TypechangesModify(Ec2TypechangesBase):
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
            'EventTime': ts_obj, # ts_str,
            'ResourceName': rp_dict['instanceId'],
            'ResourceSize1': newType,
          }

          return result


class RedshiftTypechangesResize(Ec2TypechangesBase):
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
            'EventTime': ts_obj, # ts_str,
            'ResourceName': rp_dict['clusterIdentifier'],
            'ResourceSize1': nodeType,
            'ResourceSize2': numberOfNodes,

          }

          return result


class GeneralManager:
    def ec2_typeChanges(self):
        import pandas as pd
        from termcolor import colored
        import botocore
        import sys

        def run_iterator(man2_i):
          try:
            r_i = list(man2_i.iterate_event())
          except botocore.exceptions.ClientError as e:
            logger.error(colored("\n"+str(e), 'red'))
            sys.exit(1)

          return r_i

        man2_ec2run = Ec2TypechangesRun()
        r_ec2run = run_iterator(man2_ec2run)
        
        man2_ec2mod = Ec2TypechangesModify()
        r_ec2mod = run_iterator(man2_ec2mod)
       
        man2_rscre = RedshiftTypechangesCreate()
        r_rscre = run_iterator(man2_rscre)

        man2_rsmod = RedshiftTypechangesResize()
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


if __name__=='__main__':
    man1 = GeneralManager()
    df = man1.ec2_typeChanges()
    print("")
    print(df)
