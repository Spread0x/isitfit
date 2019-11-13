# Related
# https://docs.datadoghq.com/integrations/amazon_redshift/
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/redshift.html#Redshift.Paginator.DescribeClusters

from termcolor import colored

import logging
logger = logging.getLogger('isitfit')


class ReporterBase:
  def set_analyzer(self, analyzer):
    self.analyzer = analyzer

  def postprocess(self):
    raise Exception("To be implemented by derived class")

  def display(self):
    raise Exception("To be implemented by derived class")

  def email(self):
    raise Exception("To be implemented by derived class")


class ReporterAnalyze(ReporterBase):
  def postprocess(self):
    # copied from isitfit.cost.utilizationListener.after_all
    cwau_val = self.analyzer.cwau_percent
    cwau_color = 'yellow'
    if cwau_val >= 70: cwau_color = 'green'
    elif cwau_val <= 30: cwau_color = 'red'

    dt_start = self.analyzer.rp_iter.StartTime.strftime("%Y-%m-%d")
    dt_end   = self.analyzer.rp_iter.EndTime.strftime("%Y-%m-%d")

    self.table = [
      { 'color': '',
        'label': "Start date",
        'value': "%s"%dt_start
      },
      { 'color': '',
        'label': "End date",
        'value': "%s"%dt_end
      },
      { 'color': '',
        'label': "Regions",
        'value': "%i"%self.analyzer.regions_n
      },
      { 'color': '',
        'label': "Redshift clusters (total)",
        'value': "%i"%self.analyzer.n_rc_total
      },
      { 'color': '',
        'label': "Redshift clusters (analysed)",
        'value': "%i"%self.analyzer.n_rc_analysed
      },
      { 'color': '',
        'label': "Billed cost",
        'value': "%0.0f $"%self.analyzer.cost_billed
      },
      { 'color': '',
        'label': "Used cost",
        'value': "%0.0f $"%self.analyzer.cost_used
      },
      { 'color': cwau_color,
        'label': "CWAU",
        'value': "%0.0f %%"%cwau_val
      },
    ]


  def display(self, *args, **kwargs):
    # copied from isitfit.cost.utilizationListener.display_all

    def get_row(row):
        def get_cell(i):
          retc = row[i] if not row['color'] else colored(row[i], row['color'])
          return retc

        retr = [get_cell('label'), get_cell('value')]
        return retr

    dis_tab = [get_row(row) for row in self.table]

    # warn missing data
    rc_noData = self.analyzer.rp_iter.rc_noData
    warning_noData = "Redshift clusters without data (%i): %s..."%(len(rc_noData), ", ".join(rc_noData[:5]))
    logger.warning(warning_noData)

    from tabulate import tabulate

    # logger.info("Summary:")
    logger.info("Cost-Weighted Average Utilization (CWAU) of the AWS Redshift account:")
    logger.info("")
    logger.info(tabulate(dis_tab, headers=['Field', 'Value']))
    logger.info("")
    logger.info("For reference:")
    logger.info(colored("* CWAU >= 70% is well optimized", 'green'))
    logger.info(colored("* CWAU <= 30% is underused", 'red'))
    logger.info("")
    logger.info("For the EC2 analysis, scroll up to the previous table.")


  def email(self, emailTo):
      from ...emailMan import EmailMan
      em = EmailMan(
        dataType='cost analyze', # redshift, not ec2
        dataVal={'table': self.table},
        ctx=None
      )
      em.send(emailTo)




class ReporterOptimize(ReporterBase):
  def postprocess(self):
    analyze_df = self.analyzer.analyze_df
    analyze_df['CpuMaxMax'] = analyze_df['CpuMaxMax'].fillna(value=0).astype(int)
    analyze_df['CpuMinMin'] = analyze_df['CpuMinMin'].fillna(value=0).astype(int)

    # copied from isitfit.cost.optimizationListener.storecsv...
    import tempfile
    with tempfile.NamedTemporaryFile(prefix='isitfit-full-redshift-', suffix='.csv', delete=False) as  csv_fh_final:
      self.csv_fn_final = csv_fh_final.name
      logger.debug(colored("Saving final results to %s"%csv_fh_final.name, "cyan"))
      analyze_df.to_csv(csv_fh_final.name, index=False)
      logger.debug(colored("Save complete", "cyan"))


  def display(self):
    # copied from isitfit.cost.optimizationListener.display_all
    analyze_df = self.analyzer.analyze_df

    # display dataframe
    from ...utils import display_df
    display_df(
      "Redshift cluster classifications",
      analyze_df,
      self.csv_fn_final,
      analyze_df.shape,
      logger
    )


  def email(self, emailTo):
      raise Exception("Error emailing optimization: Not yet implemented")
