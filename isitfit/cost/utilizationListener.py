import logging
logger = logging.getLogger('isitfit')

import pandas as pd
from tabulate import tabulate

# https://pypi.org/project/termcolor/
from termcolor import colored


class UtilizationListener:

  def __init__(self, emailTo, ctx):
    # iterate over all ec2 instances
    self.sum_capacity = 0
    self.sum_used = 0
    self.df_all = []
    self.table = None # will contain the final table after calling `after_all`
    self.emailTo = emailTo
    self.ctx = ctx


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
            {'color': '',         'label': "Start date",              'value': "%s"%dt_start                },
            {'color': '',         'label': "End date",                'value': "%s"%dt_end                  },
            {'color': '',         'label': "EC2 machines (total)",    'value': "%i"%n_ec2_total             },
            {'color': '',         'label': "EC2 machines (analysed)", 'value': "%i"%n_ec2_analysed          },
            {'color': 'cyan',     'label': "Billed cost",             'value': "%0.0f $"%self.sum_capacity  },
            {'color': 'cyan',     'label': "Used cost",               'value': "%0.0f $"%self.sum_used      },
            {'color': cwau_color, 'label': "CWAU (Used/Billed)",      'value': "%0.0f %%"%cwau_val          },
    ]


  def display_all(self, *args, **kwargs):
    def get_row(row):
        def get_cell(i):
          retc = row[i] if not row['color'] else colored(row[i], row['color'])
          return retc
        
        retr = [get_cell('label'), get_cell('value')]
        return retr

    dis_tab = [get_row(row) for row in self.table]

    # logger.info("Summary:")
    logger.info("Cost-Weighted Average Utilization (CWAU) of the AWS EC2 account:")
    logger.info("")
    logger.info(tabulate(dis_tab, headers=['Field', 'Value']))
    logger.info("")
    logger.info("For reference:")
    logger.info(colored("* CWAU >= 70% is well optimized", 'green'))
    logger.info(colored("* CWAU <= 30% is underused", 'red'))

  def share_email(self, *args, **kwargs):
      # check if email requested
      if self.emailTo is None:
          return

      if len(self.emailTo)==0:
          return

      from ..emailMan import EmailMan
      em = EmailMan(
        dataType='cost analyze',
        dataVal={'table': self.table},
        ctx=self.ctx
      )
      em.send(self.emailTo)


