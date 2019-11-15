# AWS_DEFAULT_REGION=us-east-2 python3 -m isitfit.cost.test_redshift
# Related
# https://docs.datadoghq.com/integrations/amazon_redshift/
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/redshift.html#Redshift.Paginator.DescribeClusters

from tqdm import tqdm
import pandas as pd

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
#redshiftPricing_df = [{'NodeType': k, 'Cost': v} for k, v in redshiftPricing_dict.items()]
#redshiftPricing_df = pd.DataFrame(redshiftPricing_df)
#print("redshift pricing")
#print(redshiftPricing_df)



class AnalyzerBase:
  n_rc_total = 0
  n_rc_analysed = 0

  def __init__(self):
    # define the list in the constructor because if I define it as a class member above,
    # then it gets reused between instantiations of derived classes
    self.analyze_list = []
    self.analyze_df = None

  def set_iterator(self, rp_iter):
    """
    rp_iter - from .iterator import RedshiftPerformanceIterator
    """
    self.rp_iter = rp_iter

  def count(self):
    # count clusters
    for rc_describe_entry in self.rp_iter.iterate_core(True, True):
      self.n_rc_total += 1

  def iterator(self):
    # get all performance dataframes, on the cluster-aggregated level
    for rc_describe_entry, df_single in tqdm(self.rp_iter, desc="%s, fetching CPU metrics"%self.rp_iter.service_description, total=self.n_rc_total):

      # for types not yet in pricing dictionary above
      rc_type = rc_describe_entry['NodeType']
      if rc_type not in redshiftPricing_dict.keys():
        rc_id = rc_describe_entry['ClusterIdentifier']
        self.rp_iter.rc_noData.append(rc_id)
        continue

      yield rc_describe_entry, df_single

  def fetch(self):
    # To be used by derived class *after* its own implementation

    # gather into a single dataframe
    self.analyze_df = pd.DataFrame(self.analyze_list)

    # update number of analyzed clusters
    self.n_rc_analysed = self.analyze_df.shape[0]

  def calculate(self):
    raise Exception("To be implemented by derived class")



class AnalyzerAnalyze(AnalyzerBase):

  def fetch(self):
    # get all performance dataframes, on the cluster-aggregated level
    import datetime as dt
    import pytz
    import math
    dt_now_d = dt.datetime.utcnow().replace(tzinfo=pytz.utc)

    for rc_describe_entry, df_single in self.iterator():
      rc_type = rc_describe_entry['NodeType']

      # append a n_hours field per day
      # and correct for number of hours on first and last day
      # Note that intermediate days are just 24 hours since Redshift cannot be stopped
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

      # summarize into 1 row
      self.analyze_list.append({
        'ClusterIdentifier': rc_describe_entry['ClusterIdentifier'],
        'NodeType': rc_type,
        'NumberOfNodes': rc_describe_entry['NumberOfNodes'],
        'Region': rc_describe_entry['Region'],

        # TODO if cloudtrail is used to get the history of size changes of a redshift cluster,
        # the pricing field needs to change from a single number to a series of same dimension as df_single.Average
        # The same applies to the number of nodes field, which becomes a series too.
        # Finally, the "* df_single.shape[0]" becomes ".sum()"
        'CostUsed':   (df_single.Average / 100 * redshiftPricing_dict[rc_type] * df_single.n_hours * rc_describe_entry['NumberOfNodes']).sum(),
        'CostBilled': (1                       * redshiftPricing_dict[rc_type] * df_single.n_hours * rc_describe_entry['NumberOfNodes']).sum()
      })

    # done
    super().fetch()


  def calculate(self):
    # calculate cost-weighted utilization
    analyze_df = self.analyze_df
    self.cost_used   = analyze_df.CostUsed.fillna(value=0).sum()
    self.cost_billed = analyze_df.CostBilled.fillna(value=0).sum()
    self.regions_n = len(analyze_df.Region.unique())

    if self.cost_billed == 0:
      self.cwau_percent = 0
      return

    self.cwau_percent = int(self.cost_used / self.cost_billed * 100)


class AnalyzerOptimize(AnalyzerBase):

  def fetch(self):

    # get all performance dataframes, on the cluster-aggregated level
    for rc_describe_entry, df_single in self.iterator():

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
    super().fetch()



  def calculate(self):
    def classify_cluster_single(row):
        # classify
        if row.CpuMinMin > 70: return "Overused"
        if row.CpuMaxMax <  5: return "Idle"
        if row.CpuMaxMax < 30: return "Underused"
        return "Normal"

    # convert percentages to int since fractions are not very useful
    analyze_df = self.analyze_df
    analyze_df['classification'] = analyze_df.apply(classify_cluster_single, axis=1)

