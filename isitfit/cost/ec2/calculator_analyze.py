import logging
logger = logging.getLogger('isitfit')

import pandas as pd
from tabulate import tabulate

# https://pypi.org/project/termcolor/
from termcolor import colored



class CalculatorAnalyzeEc2:

  def __init__(self, ctx, save_details):
    # iterate over all ec2 instances
    self.sum_capacity = 0
    self.sum_used = 0
    self.df_all = []
    self.table = None # will contain the final table after calling `after_all`
    self.ctx = ctx

    # saving details to CSV
    self.save_details = save_details
    self.csv_fn_intermediate = None
    self.csv_fn_empty = True


  def handle_pre(self, context_pre):
    if not self.save_details: return context_pre
    import tempfile
    csvi_prefix = 'isitfit-cost-analyze-ec2-details-1-'
    self.csv_fn_intermediate = tempfile.NamedTemporaryFile(prefix=csvi_prefix, suffix='.csv', delete=False)
    return context_pre


  def per_ec2(self, context_ec2):
    """
    Listener function to be called upon the download of each EC2 instance's data
    ec2_obj - boto3 resource
    ec2_df - pandas dataframe with data from cloudwatch+cloudtrail
    mm - mainManager class
    ddg_df - dataframe of data from datadog: {cpu,ram}-{max,avg}
    """
    # parse out context keys
    ec2_obj, ec2_df, mm, ddg_df = context_ec2['ec2_obj'], context_ec2['ec2_df'], context_ec2['mainManager'], context_ec2['ddg_df']

    # results: 2 numbers: capacity (USD), used (USD)
    res_capacity = (ec2_df.nhours*ec2_df.cost_hourly).sum()

    if 'ram_used_avg.datadog' in ec2_df.columns:
      # use both the CPU Average from cloudwatch and the RAM average from datadog
      utilization_factor = ec2_df[['Average', 'ram_used_avg.datadog']].mean(axis=1, skipna=True)
    else:
      # use only the CPU average from cloudwatch
      utilization_factor = ec2_df.Average

    res_used     = (ec2_df.nhours*ec2_df.cost_hourly*utilization_factor/100).sum()
    #logger.debug("res_capacity=%s, res_used=%s"%(res_capacity, res_used))

    self.sum_capacity += res_capacity
    self.sum_used += res_used
    self.df_all.append({'instance_id': ec2_obj.instance_id, 'capacity': res_capacity, 'used': res_used})

    # check if save details
    # http://stackoverflow.com/questions/17530542/ddg#17975690
    if self.save_details:
      ec2_df.to_csv(
        path_or_buf = self.csv_fn_intermediate.name,
        mode = 'w' if self.csv_fn_empty else 'a',
        header = self.csv_fn_empty,
        index = False
      )
      self.csv_fn_empty = False

    return context_ec2


  def after_all(self, context_all):
    # for debugging
    df_all = pd.DataFrame(self.df_all)
    logger.debug("\ncapacity/used per instance")
    logger.debug(df_all)
    logger.debug("\n")

    # set n analysed
    context_all['n_ec2_analysed'] = len(self.df_all)

    # dump to csv for details
    if self.save_details:
      # display message for first file
      csvi_desc ='Per ec2 and day'
      msg_info = "Detail file 1/2: %s: %s"%(csvi_desc, self.csv_fn_intermediate.name)
      msg_info = colored(msg_info, "cyan")
      logger.info(msg_info)

      # save 2nd file and display message
      import tempfile
      csvi_prefix = 'isitfit-cost-analyze-ec2-details-2-'
      csv_fh_final = tempfile.NamedTemporaryFile(prefix=csvi_prefix, suffix='.csv', delete=False)

      df_all.to_csv(csv_fh_final.name, index=False)

      # display message about 2nd file
      csvi_desc = 'Per ec2 only   ' # 3 spaces just to align with "per ec2 and day
      msg_info = "Detail file 2/2: %s: %s"%(csvi_desc, csv_fh_final.name)
      msg_info = colored(msg_info, "cyan")
      logger.info(msg_info)

    return context_all
