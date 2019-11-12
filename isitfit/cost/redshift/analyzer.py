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



class Analyzer:
  n_rc_total = 0
  n_rc_analysed = 0

  def __init__(self, rp_iter):
    """
    rp_iter - from .iterator import RedshiftPerformanceIterator
    """
    self.rp_iter = rp_iter

  def fetch_count(self):
    # count clusters
    for rc_describe_entry in tqdm(self.rp_iter.iterate_core(), desc="Redshift clusters, pass 1/2"):
      self.n_rc_total += 1

  def fetch_performances(self):
    # get all performance dataframes, on the cluster-aggregated level
    analyze_list = []
    for rc_describe_entry, df_single in tqdm(self.rp_iter, desc="Redshift clusters, pass 2/2", total=self.n_rc_total):
    
      # for types not yet in pricing dictionary above
      rc_id = rc_describe_entry['ClusterIdentifier']
      rc_type = rc_describe_entry['NodeType']
      if rc_type not in redshiftPricing_dict.keys():
        self.rp_iter.rc_noData.append(rc_id)
        continue
    
      # summarize into maxmax, maxmin, minmax, minmin
      analyze_list.append({
        'ClusterIdentifier': rc_id,
        'NodeType': rc_type,
        'NumberOfNodes': rc_describe_entry['NumberOfNodes'],
        'CpuMaxMax': df_single.Maximum.max(),
        #'CpuMaxMin': df_single.Maximum.min(),
        #'CpuMinMax': df_single.Minimum.max(),
        'CpuMinMin': df_single.Minimum.min(),
        'Cost': redshiftPricing_dict[rc_type],
      })

    # gather into a single dataframe
    self.analyze_df = pd.DataFrame(analyze_list)

    # update number of analyzed clusters
    self.n_rc_analysed = self.analyze_df.shape[0]
 

  def calculate_cwau(self):  
    # calculate cost-weighted utilization
    analyze_df = self.analyze_df
    cwau_numerator = (analyze_df.CpuMaxMax * analyze_df.Cost * analyze_df.NumberOfNodes).sum()
    cwau_denominator = (analyze_df.Cost * analyze_df.NumberOfNodes).sum()
    cwau_percent = cwau_numerator / cwau_denominator # since CpuMaxMax is in percentage, this will be in percentage also
    cwau_percent = int(cwau_percent)
    self.cwau_percent = cwau_percent


  def classify(self):
    def classify_cluster_single(row):
        # classify
        if row.CpuMinMin > 70: return "Overused"
        if row.CpuMaxMax <  5: return "Idle"
        if row.CpuMaxMax < 30: return "Underused"
        return "Normal"

    # convert percentages to int since fractions are not very useful
    analyze_df = self.analyze_df
    analyze_df['classification'] = analyze_df.apply(classify_cluster_single, axis=1)

