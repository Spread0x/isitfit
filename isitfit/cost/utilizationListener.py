import logging
logger = logging.getLogger('isitfit')

import pandas as pd
from tabulate import tabulate

# https://pypi.org/project/termcolor/
from termcolor import colored


class UtilizationListener:

  def __init__(self):
    # iterate over all ec2 instances
    self.sum_capacity = 0
    self.sum_used = 0
    self.df_all = []
    self.table = None # will contain the final table after calling `after_all`


  def per_ec2(self, ec2_obj, ec2_df, mm, ddg_df):
    """
    Listener function to be called upon the download of each EC2 instance's data
    ec2_obj - boto3 resource
    ec2_df - pandas dataframe with data from cloudwatch+cloudtrail
    mm - mainManager class
    ddg_df - dataframe of data from datadog: {cpu,ram}-{max,avg}
    """
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


  def after_all(self, n_ec2_total, mm, n_ec2_analysed):
    # for debugging
    df_all = pd.DataFrame(self.df_all)
    logger.debug("\ncapacity/used per instance")
    logger.debug(df_all)
    logger.debug("\n")

    cwau_val = 0
    if self.sum_capacity!=0:
      cwau_val = self.sum_used/self.sum_capacity*100

    cwau_color = 'orange'
    if cwau_val >= 70:
      cwau_color = 'green'
    elif cwau_val <= 30:
      cwau_color = 'red'

    dt_start = mm.StartTime.strftime("%Y-%m-%d")
    dt_end   = mm.EndTime.strftime("%Y-%m-%d")
    
    self.table = [
      ["Start date", "%s"%dt_start],
      ["End date", "%s"%dt_end],
      ["EC2 machines (total)", "%i"%n_ec2_total],
      ["EC2 machines (analysed)", "%i"%n_ec2_analysed],
      [colored("Billed cost", 'cyan'), colored("%0.0f $"%self.sum_capacity, 'cyan')],
      [colored("Used cost", 'cyan'), colored("%0.0f $"%self.sum_used, 'cyan')],
      [colored("CWAU (Used/Billed)", cwau_color), colored("%0.0f %%"%cwau_val, cwau_color)],
    ]


  def display_all(self, *args, **kwargs):
    # logger.info("Summary:")
    logger.info("Cost-Weighted Average Utilization (CWAU) of the AWS EC2 account:")
    logger.info("")
    logger.info(tabulate(self.table, headers=['Field', 'Value']))
    logger.info("")
    logger.info("For reference:")
    logger.info(colored("* CWAU >= 70% is well optimized", 'green'))
    logger.info(colored("* CWAU <= 30% is underused", 'red'))

