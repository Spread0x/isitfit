import boto3
import pandas as pd
import requests


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


class MainManager:
    def __init__(self):
        self.ec2_client = boto3.client('ec2')
        self.cloudwatch_client = boto3.client('cloudwatch')
        self.cloudtrail_client = boto3.client('cloudtrail')


    def get_ifi(self):
        # download ec2 catalog: 2 columns: ec2 type, ec2 cost per hour
        self.df_cat = pd.read_csv(requests.open('s3://catalog.csv'))

        # iterate over all ec2 instances
        ec2_client = boto3.client('ec2')
        cloudwatch_client = boto3.client('cloudwatch')
        cloudtrail_client = boto3.client('cloudtrail')

        sum_capacity = 0
        sum_used = 0
        for ec2_obj in ec2_client.instances():
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


    def _handle_ec2obj(self, ec2_obj):
        # pandas series of CPU utilization, daily max, for 90 days
        series_pcpu = self.cloudwatch_client.get_metric(ec2_obj.id, 'cpu daily max percentage for 90 days')

        # pandas series of number of 5-min intervals per day (to show how long the machine was running on that day)
        series_n5mn = self.cloudwatch_client.get_metric(ec2_obj.id, 'count')

        # pandas series of number of cpu's available on the machine over time, past 90 days
        series_type_ts1 = self.cloudtrail_client.get_ec2_type(ec2_obj.id)

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
