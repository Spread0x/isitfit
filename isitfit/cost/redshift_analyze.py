from isitfit.utils import logger






def get_dtNowD():
  import datetime as dt
  import pytz
  dt_now_d = dt.datetime.utcnow().replace(tzinfo=pytz.utc)
  return dt_now_d


import math
dt_now_d = get_dtNowD()

from isitfit.utils import mergeSeriesOnTimestampRange


# convert above dict to pandas dataframe
from isitfit.cost.catalog_redshift import redshiftPricing_df



from isitfit.cost.redshift_common import CalculatorBaseRedshift
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

      # append a nhours field per day
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
      #     Timestamp  SampleCount   Average   Minimum    Maximum     Unit  nhours
      # 2  2019-11-19        918.0  2.324190  0.833333  53.500000  Percent       24
      # 0  2019-11-20          4.0  1.208333  1.000000   1.416667  Percent        4
      #
      # Update 2019-12-17 It turns out SampleCount for redshift is 1 per 10 minutes (wherease EC2 is 1 per 5 minutes)
      # Commenting out the nhours calculation below and no need to add new calculation because Cloudwatch metrics class will already add the nhours field
      #ymd_creation = rc_describe_entry['ClusterCreateTime'].strftime("%Y-%m-%d")
      #ymd_today    = dt_now_d.strftime("%Y-%m-%d")
      #
      #hc_ref = dt_now_d if ymd_creation == ymd_today else rc_describe_entry['ClusterCreateTime'].replace(hour=23, minute=59)
      #hours_creation = hc_ref - rc_describe_entry['ClusterCreateTime']
      #hours_creation = math.ceil(hours_creation.seconds/60/60)
      #hours_today = dt_now_d - dt_now_d.replace(hour=0, minute=0)
      #hours_today = math.ceil(hours_today.seconds/60/60)
      #
      #def calc_nhours(ts):
      #  ts_str = ts.strftime("%Y-%m-%d")
      #  if ts_str == ymd_creation: return hours_creation
      #  if ts_str == ymd_today:    return hours_today
      #  return 24
      #
      #df_single['nhours'] = df_single.Timestamp.apply(calc_nhours)

      # merge df_single (metrics) with df_type_ts1 (cloudtrail history)
      # (adds column NodeType, NumberOfNodes)
      df_single = mergeSeriesOnTimestampRange(df_single, df_type_ts1, ['NodeType', 'NumberOfNodes'])

      # merge with the price catalog (adds column Cost)
      df_single = df_single.merge(redshiftPricing_df, left_on='NodeType', right_on='NodeType', how='left')

      # calculate columns capacity_usd and used_usd
      df_single['used_usd'    ] = df_single.cpu_used_avg / 100 * df_single.Cost * df_single.nhours * df_single.NumberOfNodes
      df_single['capacity_usd'] = 1                       * df_single.Cost * df_single.nhours * df_single.NumberOfNodes

      # save back to context for further binning
      context_ec2['df_single'] = df_single

      # summarize into 1 row
      self.analyze_list.append({
        'ClusterIdentifier': rc_describe_entry['ClusterIdentifier'],

        # most recent node type and number of nodes
        'NodeType': rc_type,
        'NumberOfNodes': rc_describe_entry['NumberOfNodes'],
        'Region': rc_describe_entry['Region'],

        # cost used/billed, including cloudtrail history
        'CostUsed':   df_single['used_usd'    ].sum(),
        'CostBilled': df_single['capacity_usd'].sum()
      })

      # done
      return context_ec2



  def calculate(self, context_all):
    # defaults
    self.cost_used = 0
    self.cost_billed = 0
    self.cwau_percent = 0
    self.regions_n = 0

    # calculate cost-weighted utilization
    analyze_df = self.analyze_df

    # no data, eg when ndays=1 and a cluster is launched a few minutes ago,
    # cloudwatch has a bug whereby it doesn't return today's data anymore.
    # Need to set ndays>=64 to get today's data. Check related bugfix in ec2_analyze
    if analyze_df.shape[0]==0:
      return context_all

    self.cost_used   = analyze_df.CostUsed.fillna(value=0).sum()
    self.cost_billed = analyze_df.CostBilled.fillna(value=0).sum()
    self.regions_n = len(analyze_df.Region.unique())

    if self.cost_billed == 0:
      self.cwau_percent = 0
      return context_all

    self.cwau_percent = int(self.cost_used / self.cost_billed * 100)
    return context_all





from isitfit.cost.base_reporter import ReporterBase
class ReporterAnalyze(ReporterBase):
  def postprocess(self, context_all):
    # unpack
    self.analyzer = context_all['analyzer']
    mm = context_all['mainManager']
    n_rc_total = context_all['n_ec2_total']
    n_rc_analysed = context_all['n_rc_analysed']

    # copied from isitfit.cost.ec2.calculator_analyze.after_all
    cwau_val = self.analyzer.cwau_percent
    cwau_color = 'yellow'
    if cwau_val >= 70: cwau_color = 'green'
    elif cwau_val <= 30: cwau_color = 'red'

    dt_start = mm.StartTime.strftime("%Y-%m-%d")
    dt_end   = mm.EndTime.strftime("%Y-%m-%d")

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
        'value': "%i"%n_rc_total
      },
      { 'color': '',
        'label': "Redshift clusters (analyzed)",
        'value': "%i"%n_rc_analysed
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
        'label': "CWAU (Used/Billed)",
        'value': "%0.0f %%"%cwau_val
      },
    ]

    # save in context for aggregator
    context_all['table'] = self.table

    # done
    return context_all

# DEPRECATED in favor of the reporter in account_cost_analyze.py
#
#  def display(self, context_all):
#    # copied from isitfit.cost.ec2.calculator_analyze.display_all
#
#    # https://pypi.org/project/termcolor/
#    from termcolor import colored
#
#    def get_row(row):
#        def get_cell(i):
#          retc = row[i] if not row['color'] else colored(row[i], row['color'])
#          return retc
#
#        retr = [get_cell('label'), get_cell('value')]
#        return retr
#
#    dis_tab = [get_row(row) for row in self.table]
#
#    from tabulate import tabulate
#
#    # logger.info("Summary:")
#    logger.info("Cost-Weighted Average Utilization (CWAU) of the AWS Redshift account:")
#    logger.info("")
#    logger.info(tabulate(dis_tab, headers=['Field', 'Value']))
#    logger.info("")
#    logger.info("For reference:")
#    logger.info(colored("* CWAU >= 70% is well optimized", 'green'))
#    logger.info(colored("* CWAU <= 30% is underused", 'red'))
#    logger.info("")
#    logger.info("For the EC2 analysis, scroll up to the previous table.")
#    return context_all
#
#
#  def email(self, context_all):
#      context_2 = {}
#      context_2['emailTo'] = context_all['emailTo']
#      context_2['click_ctx'] = context_all['click_ctx']
#      context_2['dataType'] = 'cost analyze' # redshift, not ec2
#      context_2['dataVal'] = {'table': self.table}
#      super().email(context_2)
#
#      return context_all




def pipeline_factory(share_email, filter_region, ctx, filter_tags):
  # This is a factory method, so it doesn't make sense to display "Analyzing bla" if actually "foo" is analyzed first
  #logger.info("Analyzing redshift clusters")

  from .redshift_common import redshift_cost_core
  ra = CalculatorAnalyzeRedshift()
  rr = ReporterAnalyze()
  mm = redshift_cost_core(ra, rr, share_email, filter_region, ctx, filter_tags)
  return mm

