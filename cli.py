import boto3
import pandas as pd
import requests
from cachecontrol import CacheControl
from tqdm import tqdm
import datetime as dt
from gitRemoteAws.pull_cloudtrail_lookupEvents import GeneralManager as CloudtrailManager
import os


def matchSeries(series_cpu, series_type):
  """
  Upsamples series_type to series_cpu.
  Example:
    Input
      series_pcpu = pd.Series({'time': [1,2,3,4], 'value': [5,6,7,8]})
      series_type = pd.Series({'time': [1,3], 'value': ['a','b']})
    Returns
      pd.Series({'time': [1,2,3,4], 'value': ['a','a','b','b']})
  """
  return series_type


SECONDS_IN_ONE_DAY = 60*60*24 # 86400  # used for granularity (daily)
N_DAYS=90

class MainManager:
    def __init__(self):
        self.ec2_resource = boto3.resource('ec2')
        self.cloudwatch_resource = boto3.resource('cloudwatch')

        self.cloudtrail_client = boto3.client('cloudtrail')

        dt_now_d=dt.datetime.now()
        self.StartTime=dt_now_d - dt.timedelta(days=N_DAYS)
        self.EndTime=dt_now_d
        # print(self.StartTime, self.EndTime)


    def get_ifi(self):
        # download ec2 catalog: 2 columns: ec2 type, ec2 cost per hour
        # FIXME # self.df_cat = self._ec2_catalog()

        # get cloudtail ec2 type changes for all instances
        cache_fn = '/tmp/isitfit_cloudtrail.csv'
        if os.path.exists(cache_fn):
            print("Loading cloudtrail data from cache")
            self.df_cloudtrail = pd.read_csv(cache_fn).set_index(["instanceId", "EventTime"])
        else:
            print("Downloading cloudtrail data")
            cloudtrail_manager = CloudtrailManager(self.cloudtrail_client)
            self.df_cloudtrail = cloudtrail_manager.ec2_typeChanges()
            self.df_cloudtrail.to_csv(cache_fn)

        # iterate over all ec2 instances
        n_ec2 = len(list(self.ec2_resource.instances.all()))
        sum_capacity = 0
        sum_used = 0
        for ec2_obj in tqdm(self.ec2_resource.instances.all(), total=n_ec2, desc="EC2 instance", initial=1):
            res_capacity, res_used = self._handle_ec2obj(ec2_obj)
            sum_capacity += res_capacity
            sum_used += res_used

        if sum_capacity==0: return 0

        return sum_used/sum_capacity*100


    def _ec2_catalog(self):
        # based on URL = 'http://www.ec2instances.info/instances.json'
        URL = 's3://...csv'

        # cached https://cachecontrol.readthedocs.io/en/latest/
        sess = requests.session()
        cached_sess = CacheControl(sess)
        r = cached_sess.request('get', URL)

        df = ps.read_csv(r.csv())
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
            # print(json_i)
            if len(json_i['Datapoints'])==0: continue # skip (no data)

            df_i = pd.DataFrame(json_i['Datapoints'])
            df_i = df_i[['Timestamp', 'SampleCount', 'Average']]
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


    def _cloudtrail_ec2type(self, ec2_obj):
        # pandas series of number of cpu's available on the machine over time, past 90 days
        # series_type_ts1 = self.cloudtrail_client.get_ec2_type(ec2_obj.instance_id)
        return self.df_cloudtrail.loc[ec2_obj.instance_id]


    def _handle_ec2obj(self, ec2_obj):
        print(ec2_obj.instance_id, ec2_obj.instance_type)

        # pandas series of CPU utilization, daily max, for 90 days
        df_metrics = self._cloudwatch_metrics(ec2_obj)

        # no data
        if df_metrics is None: return 0, 0

        # pandas series of number of cpu's available on the machine over time, past 90 days
        series_type_ts1 = self._cloudtrail_ec2type(ec2_obj)

        # convert type timeseries to the same timeframes as pcpu and n5mn
        series_type_ts2 = matchSeries(series_pcpu, series_type_ts1)

        # bring it altogether
        ec2_df = pd.DataFrame({'pcpu': series_pcpu, 'n5mn': series_n5mn, 'type': series_type_ts2})

        # merge with catalog
        ec2_df = ec2_df.merge(self.df_cat, left_on='type', right_on='type', how='left')

        # results: 2 numbers: capacity (USD), used (USD)
        ec2_df.nhours = math.ceil(ec2_df.n5mn/12)
        res_capacity = (ec2_df.nhours*ec2_df.cost_hourly).sum()
        res_used     = (ec2_df.nhours*ec2_df.cost_hourly*ec2_df.pcpu).sum()
        return res_capacity, res_used



if __name__=='__main__':
    mm = MainManager()
    ifi = mm.get_ifi()
