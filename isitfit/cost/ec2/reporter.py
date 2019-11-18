import logging
logger = logging.getLogger('isitfit')

import pandas as pd
from tabulate import tabulate

# https://pypi.org/project/termcolor/
from termcolor import colored

from isitfit.cost.redshift.reporter import ReporterBase

class ReporterAnalyzeEc2(ReporterBase):

  def postprocess(self):
    cwau_val = 0
    if self.analyzer.sum_capacity!=0:
      cwau_val = self.analyzer.sum_used/self.analyzer.sum_capacity*100

    cwau_color = 'yellow'
    if cwau_val >= 70:
      cwau_color = 'green'
    elif cwau_val <= 30:
      cwau_color = 'red'

    dt_start = self.analyzer.mm.StartTime.strftime("%Y-%m-%d")
    dt_end   = self.analyzer.mm.EndTime.strftime("%Y-%m-%d")

    ri_max = 3
    ri_ell = "" if len(self.analyzer.region_include)<=ri_max else "..."
    ri_str = ", ".join(self.analyzer.region_include[:ri_max])+ri_ell
    
    self.table = [
            {'color': '',
             'label': "Start date",
             'value': "%s"%dt_start
            },
            {'color': '',
             'label': "End date",
             'value': "%s"%dt_end
            },
            {'color': '',
             'label': "Regions",
             'value': "%i (%s)"%(len(self.analyzer.region_include), ri_str)
            },
            {'color': '',
             'label': "EC2 machines (total)",
             'value': "%i"%self.analyzer.n_ec2_total
            },
            {'color': '',
             'label': "EC2 machines (analysed)",
             'value': "%i"%self.analyzer.n_ec2_analysed
            },
            {'color': 'cyan',
             'label': "Billed cost",
             'value': "%0.0f $"%self.analyzer.sum_capacity
            },
            {'color': 'cyan',
             'label': "Used cost",
             'value': "%0.0f $"%self.analyzer.sum_used
            },
            {'color': cwau_color,
             'label': "CWAU (Used/Billed)",
             'value': "%0.0f %%"%cwau_val
            },
    ]


  def display(self, *args, **kwargs):
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

  def email(self, emailTo):
      # check if email requested
      if emailTo is None:
          return

      if len(emailTo)==0:
          return

      from ..emailMan import EmailMan
      em = EmailMan(
        dataType='cost analyze', # ec2, not redshift
        dataVal={'table': self.table},
        ctx=self.ctx
      )
      em.send(emailTo)


