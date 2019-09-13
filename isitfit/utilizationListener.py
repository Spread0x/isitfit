import logging
logger = logging.getLogger('isitfit')

import pandas as pd
from tabulate import tabulate


class UtilizationListener:

  def __init__(self):
    # iterate over all ec2 instances
    self.sum_capacity = 0
    self.sum_used = 0
    self.df_all = []


  def per_ec2(self, ec2_obj, ec2_df):
    # results: 2 numbers: capacity (USD), used (USD)
    res_capacity = (ec2_df.nhours*ec2_df.cost_hourly).sum()
    res_used     = (ec2_df.nhours*ec2_df.cost_hourly*ec2_df.Average/100).sum()
    logger.debug("res_capacity=%s, res_used=%s"%(res_capacity, res_used))

    self.sum_capacity += res_capacity
    self.sum_used += res_used
    self.df_all.append({'instance_id': ec2_obj.instance_id, 'capacity': res_capacity, 'used': res_used})


  def after_all(self, n_ec2, mm):
    # for debugging
    df_all = pd.DataFrame(self.df_all)
    logger.debug("\ncapacity/used per instance")
    logger.debug(df_all)
    logger.debug("\n")

    cwau = 0
    if self.sum_capacity!=0:
      cwau = self.sum_used/self.sum_capacity*100

    dt_start = mm.StartTime.strftime("%Y-%m-%d")
    dt_end   = mm.EndTime.strftime("%Y-%m-%d")
    
    table = [
      ["Analysis start date", "%s"%dt_start],
      ["Analysis end date", "%s"%dt_end],
      ["Number of EC2 machines", "%i"%n_ec2],
      ["Billed cost", "%0.2f $"%self.sum_capacity],
      ["Used cost", "%0.2f $"%self.sum_used],
      ["CWAU = Used / Billed * 100", "%0.0f %%"%cwau],
    ]
    
    # logger.info("Summary:")
    logger.info("Cost-Weighted Average Utilization (CWAU) of the AWS EC2 account:")
    logger.info("")
    logger.info(tabulate(table, headers=['Field', 'Value']))
    logger.info("")
    logger.info("For reference:")
    logger.info("* CWAU >= 70% is well optimized")
    logger.info("* CWAU <= 30% is underused")

