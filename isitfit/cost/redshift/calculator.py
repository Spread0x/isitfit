# AWS_DEFAULT_REGION=us-east-2 python3 -m isitfit.cost.test_redshift
# Related
# https://docs.datadoghq.com/integrations/amazon_redshift/
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/redshift.html#Redshift.Paginator.DescribeClusters

from tqdm import tqdm
import pandas as pd
from isitfit.cost.mainManager import NoCloudwatchException
from isitfit.utils import mergeSeriesOnTimestampRange


# redshift pricing as of 2019-11-12 in USD per hour, on-demand, ohio
# https://aws.amazon.com/redshift/pricing/
redshiftPricing_dict = {
  'dc2.large': 0.25,
  'dc2.8xlarge': 4.80,
  'ds2.xlarge': 0.85,
  'ds2.8xlarge': 6.80,
  'dc1.large': 0.25,
  'dc1.8xlarge': 4.80,
}

# convert above dict to pandas dataframe
redshiftPricing_df = [{'NodeType': k, 'Cost': v} for k, v in redshiftPricing_dict.items()]
redshiftPricing_df = pd.DataFrame(redshiftPricing_df)
#print("redshift pricing")
#print(redshiftPricing_df)



class CalculatorBaseRedshift:


  def __init__(self):
    # define the list in the constructor because if I define it as a class member above,
    # then it gets reused between instantiations of derived classes
    self.analyze_list = []
    self.analyze_df = None


  def per_ec2(self, context_ec2):
      rc_describe_entry = context_ec2['ec2_dict']

      # for types not yet in pricing dictionary above
      rc_type = rc_describe_entry['NodeType']
      if rc_type not in redshiftPricing_dict.keys():
        raise NoCloudwatchException

      return context_ec2


  def after_all(self, context_all):
    # To be used by derived class *after* its own implementation

    # gather into a single dataframe
    self.analyze_df = pd.DataFrame(self.analyze_list)

    # update number of analyzed clusters
    context_all['n_rc_analysed'] = self.analyze_df.shape[0]

    # Edit 2019-11-20 no need to through exception here
    # This way, the code can proceed to show a report, and possibly proceed to other services than redshift
    #if context_all['n_rc_analysed']==0:
    #  from isitfit.utils import IsitfitCliError
    #  raise IsitfitCliError("No redshift clusters analyzed", context_all['click_ctx'])

    return context_all


  def calculate(self, context_all):
    raise Exception("To be implemented by derived class")



import datetime as dt
import pytz
import math
dt_now_d = dt.datetime.utcnow().replace(tzinfo=pytz.utc)

class CalculatorAnalyzeRedshift(CalculatorBaseRedshift):

  def per_ec2(self, context_ec2):
      # parent
      context_ec2 = super().per_ec2(context_ec2)

      # unpack
      rc_describe_entry, rc_id, rc_created = context_ec2['ec2_dict'], context_ec2['ec2_id'], context_ec2['ec2_launchtime']

      # pandas series of number of nodes available, and node type, over time, past 90 days
      df_type_ts1 = context_ec2['df_type_ts1']
      df_type_ts1 = df_type_ts1.rename(columns={'ResourceSize1': 'NodeType', 'ResourceSize2': 'NumberOfNodes'})

      # get all performance dataframes, on the cluster-aggregated level
      df_single = context_ec2['df_single']

      rc_type = rc_describe_entry['NodeType']

      # append a n_hours field per day
      # and correct for number of hours on first and last day
      # Note that intermediate days are just 24 hours since Redshift cannot be stopped
      # Update 2019-11-20
      # FIXME need to look at how to use SampleCount for this to get a more accurate number,
      # especially for days on which an instance is run for the first 10 hours then deleted
      # To note that initially I had dismissed this SampleCount idea because a redshift cluster cannot be
      # stopped and restarted like ec2, but a major difference is the ability to re-assign a past ID to the cluster
      # unlike ec2 where the instance ID gets generated randomly for each terminated and re-created instance
      # eg
      # (Pdb) df_single.head()
      #     Timestamp  SampleCount   Average   Minimum    Maximum     Unit  n_hours
      # 2  2019-11-19        918.0  2.324190  0.833333  53.500000  Percent       24
      # 0  2019-11-20          4.0  1.208333  1.000000   1.416667  Percent        4
      ymd_creation = rc_describe_entry['ClusterCreateTime'].strftime("%Y-%m-%d")
      ymd_today    = dt_now_d.strftime("%Y-%m-%d")

      hc_ref = dt_now_d if ymd_creation == ymd_today else rc_describe_entry['ClusterCreateTime'].replace(hour=23, minute=59)
      hours_creation = hc_ref - rc_describe_entry['ClusterCreateTime']
      hours_creation = math.ceil(hours_creation.seconds/60/60)
      hours_today = dt_now_d - dt_now_d.replace(hour=0, minute=0)
      hours_today = math.ceil(hours_today.seconds/60/60)

      def calc_nhours(ts):
        ts_str = ts.strftime("%Y-%m-%d")
        if ts_str == ymd_creation: return hours_creation
        if ts_str == ymd_today:    return hours_today
        return 24

      df_single['n_hours'] = df_single.Timestamp.apply(calc_nhours)

      # merge df_single (metrics) with df_type_ts1 (cloudtrail history)
      # (adds column NodeType, NumberOfNodes)
      rc_df = mergeSeriesOnTimestampRange(df_single, df_type_ts1, ['NodeType', 'NumberOfNodes'])

      # merge with the price catalog (adds column Cost)
      rc_df = rc_df.merge(redshiftPricing_df, left_on='NodeType', right_on='NodeType', how='left')

      # summarize into 1 row
      self.analyze_list.append({
        'ClusterIdentifier': rc_describe_entry['ClusterIdentifier'],

        # most recent node type and number of nodes
        'NodeType': rc_type,
        'NumberOfNodes': rc_describe_entry['NumberOfNodes'],
        'Region': rc_describe_entry['Region'],

        # cost used/billed, including cloudtrail history
        'CostUsed':   (rc_df.Average / 100 * rc_df.Cost * rc_df.n_hours * rc_df.NumberOfNodes).sum(),
        'CostBilled': (1                   * rc_df.Cost * rc_df.n_hours * rc_df.NumberOfNodes).sum()
      })

      # done
      return context_ec2



  def calculate(self, context_all):
    # calculate cost-weighted utilization
    analyze_df = self.analyze_df
    self.cost_used   = analyze_df.CostUsed.fillna(value=0).sum()
    self.cost_billed = analyze_df.CostBilled.fillna(value=0).sum()
    self.regions_n = len(analyze_df.Region.unique())

    if self.cost_billed == 0:
      self.cwau_percent = 0
      return context_all

    self.cwau_percent = int(self.cost_used / self.cost_billed * 100)
    return context_all


class CalculatorOptimizeRedshift(CalculatorBaseRedshift):

  def per_ec2(self, context_ec2):
      """
      # get all performance dataframes, on the cluster-aggregated level
      """

      # parent
      context_ec2 = super().per_ec2(context_ec2)

      # unpack
      rc_describe_entry = context_ec2['ec2_dict']
      df_single = context_ec2['df_single']

      # summarize into maxmax, maxmin, minmax, minmin
      self.analyze_list.append({
        'Region': rc_describe_entry['Region'],
        'ClusterIdentifier': rc_describe_entry['ClusterIdentifier'],
        'NodeType': rc_describe_entry['NodeType'],
        'NumberOfNodes': rc_describe_entry['NumberOfNodes'],

        'CpuMaxMax': df_single.Maximum.max(),
        #'CpuMaxMin': df_single.Maximum.min(),
        #'CpuMinMax': df_single.Minimum.max(),
        'CpuMinMin': df_single.Minimum.min(),
      })

      # done
      return context_ec2



  def calculate(self, context_all):
    def classify_cluster_single(row):
        # classify
        if row.CpuMinMin > 70: return "Overused"
        if row.CpuMaxMax <  5: return "Idle"
        if row.CpuMaxMax < 30: return "Underused"
        return "Normal"

    # convert percentages to int since fractions are not very useful
    analyze_df = self.analyze_df
    analyze_df['classification'] = analyze_df.apply(classify_cluster_single, axis=1)
    return context_all
