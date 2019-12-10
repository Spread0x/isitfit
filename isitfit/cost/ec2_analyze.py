from isitfit.utils import logger
import pandas as pd

from isitfit.cost.base_iterator import BaseIterator
class Ec2Iterator(BaseIterator):
  service_name = 'ec2'
  service_description = 'EC2 instances'
  paginator_name = 'describe_instances'
  # Notice that [] notation flattens the list of lists
  # http://jmespath.org/tutorial.html
  paginator_entryJmespath = 'Reservations[].Instances[]'
  paginator_exception = 'AuthFailure'
  entry_keyId = 'InstanceId'
  entry_keyCreated = 'LaunchTime'

  def __iter__(self):
    # over-ride the __iter__ to get the ec2 resource object for the current code (backwards compatibility)

    # method 1 for ec2
    # ec2_it = self.ec2_resource.instances.all()
    # return ec2_it

    # boto3 ec2 and cloudwatch data
    ec2_resource_all = {}
    import boto3

    # TODO cannot use directly use the iterator exposed in "ec2_it"
    # because it would return the dataframes from Cloudwatch,
    # whereas in the cloudwatch data fetch here, the data gets cached to redis.
    # Once the redshift.iterator can cache to redis, then the cloudwatch part here
    # can also be dropped, as well as using the "ec2_it" iterator directly
    # for ec2_dict in self.ec2_it:
    for ec2_dict, ec2_id, ec2_launchtime, _ in super().__iter__():
      if ec2_dict['Region'] not in ec2_resource_all.keys():
        boto3.setup_default_session(region_name = ec2_dict['Region'])
        ec2_resource_all[ec2_dict['Region']] = boto3.resource('ec2')

      ec2_resource_single = ec2_resource_all[ec2_dict['Region']]
      ec2_l = ec2_resource_single.instances.filter(InstanceIds=[ec2_dict['InstanceId']])
      ec2_l = list(ec2_l)
      if len(ec2_l)==0:
        continue # not found

      # yield first entry
      ec2_obj = ec2_l[0]
      ec2_obj.region_name = ec2_dict['Region']

      yield ec2_dict, ec2_id, ec2_launchtime, ec2_obj







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
    from isitfit.dotMan import DotMan
    csvi_prefix = 'isitfit-cost-analyze-ec2-details-1-'
    self.csv_fn_intermediate = tempfile.NamedTemporaryFile(prefix=csvi_prefix, suffix='.csv', delete=False, dir=DotMan().tempdir())
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
    ec2_df['capacity_usd'] = ec2_df.nhours*ec2_df.cost_hourly
    res_capacity = ec2_df['capacity_usd'].sum()

    if 'ram_used_avg.datadog' in ec2_df.columns:
      # use both the CPU Average from cloudwatch and the RAM average from datadog
      utilization_factor = ec2_df[['Average', 'ram_used_avg.datadog']].mean(axis=1, skipna=True)
    else:
      # use only the CPU average from cloudwatch
      utilization_factor = ec2_df.Average

    ec2_df['used_usd'] = ec2_df.nhours*ec2_df.cost_hourly*utilization_factor/100
    res_used   = ec2_df['used_usd'].sum()

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

    # save ec2_df again since added columns used and capacity
    context_ec2['ec2_df'] = ec2_df

    # done
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
      import click

      # display message for first file
      csvi_desc ='Per ec2 and day'
      msg_info = "💾 Detail file 1/2: %s: %s"%(csvi_desc, self.csv_fn_intermediate.name)
      msg_info = colored(msg_info, "cyan")
      click.echo(msg_info)

      # save 2nd file and display message
      import tempfile
      from isitfit.dotMan import DotMan
      csvi_prefix = 'isitfit-cost-analyze-ec2-details-2-'
      csv_fh_final = tempfile.NamedTemporaryFile(prefix=csvi_prefix, suffix='.csv', delete=False, dir=DotMan().tempdir())

      df_all.to_csv(csv_fh_final.name, index=False)

      # display message about 2nd file
      csvi_desc = 'Per ec2 only   ' # 3 spaces just to align with "per ec2 and day
      msg_info = "💾 Detail file 2/2: %s: %s"%(csvi_desc, csv_fh_final.name)
      msg_info = colored(msg_info, "cyan")
      click.echo(msg_info)

      click.echo(colored("Consider viewing the CSVs in the terminal with visidata: `vd file.csv` (http://visidata.org/).", "cyan"))

      click.echo("") # empty breather line
    return context_all


from isitfit.utils import pd_series_frozenset_union, l2s
class BinCapUsed:
  def __init__(self):
    # sums, in a dataframe of time bins instead of 1 global number
    self.df_bins = None
    self.context_key = 'ec2_df'

  def _set_freq(self, ndays):
    # append x more month due to pandas date_range not yielding the EOM after dt_end
    # https://stackoverflow.com/a/4406260/4126114
    #from dateutil.relativedelta import relativedelta

    # https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#offset-aliases

    if ndays <= 7:
      self.freq_start = '1D' # daily start
      self.freq_end = '1D' # daily end
      #self.freq_delta = relativedelta(days=1)
      return

    if ndays <= 30:
      self.freq_start = '1W-MON' # weekly start
      self.freq_end = '1W-SUN' # weekly end
      #self.freq_delta = relativedelta(days=7)
      return

    if ndays <= 60:
      self.freq_start = '1SMS' # semi-month start
      self.freq_end = '1SM' # semi-month end
      #self.freq_delta = relativedelta(days=15)
      return

    # otherwise monthly. Max data is 90 days from cloudwatch anyway
    self.freq_start = '1MS' # month start
    self.freq_end = '1M' # month end
    #self.freq_delta = relativedelta(months=1)
    return


  def handle_pre(self, context_pre):
    # set freq
    ndays = context_pre['mainManager'].ndays
    self._set_freq(ndays)

    # util vars
    dt_start = context_pre['mainManager'].StartTime
    dt_end   = context_pre['mainManager'].EndTime

    # set df_bins
    dt_daily = pd.date_range(start=dt_start.date(), end=dt_end.date(),  freq='1D')
    df_d1 = pd.DataFrame({
      'Timestamp': dt_daily,
      'dummy': [0]*len(dt_daily),
    })
    df_d1.set_index('Timestamp', inplace=True)
    df_d2s = df_d1.resample(self.freq_end, label='left' ).sum()
    df_d2e = df_d1.resample(self.freq_end, label='right').sum()

    # append 1 more month due to pandas date_range not yielding the EOM after dt_end
    # Update 2019-12-09 no longer needed due to usage of .resample instead of .date_range
    #dt_start2 = dt_start - self.freq_delta
    #dt_end2   = dt_end   + self.freq_delta

    # get list of dates with freq
    # https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.date_range.html
    # Update 2019-12-09 instead of using date_range to manually build the dataframe,
    # just use .resample on a dummy dataframe and pick up the index
    #dt_range_start = pd.date_range(start=dt_start2.date(), end=dt_end.date(),  freq=self.freq_start)
    #dt_range_end   = pd.date_range(start=dt_start.date(),  end=dt_end2.date(), freq=self.freq_end  )
    dt_range_start = df_d2s.reset_index().Timestamp.tolist()
    dt_range_end   = df_d2e.reset_index().Timestamp.tolist()

    # create dataframe
    self.df_bins = pd.DataFrame({
      'Timestamp': dt_range_end, # use dt_range_end in conjunction with label='right' in the .resample calls below
      'capacity_usd': 0,
      'used_usd': 0,
      'count_analyzed': 0,
      'regions_set': [frozenset([]) for x in dt_range_end], # list of sets
      'dt_start': dt_range_end, # init at end, then search for min in per_ec2
      'dt_end': dt_range_start, # init at start, then search for max in per_ec2
    })
    self.df_bins.set_index('Timestamp', inplace=True)

    return context_pre


  def per_ec2(self, context_ec2):
    if self.df_bins is None:
      raise Exception("Call handle_pre first to set the dataframe")

    ec2_df = context_ec2[self.context_key]
    df_add = ec2_df[['Timestamp', 'capacity_usd', 'used_usd']].copy()

    # index + add a duplicate column for the timestamp and use it to get min/max dates in a time bin
    df_add['Timestamp'] = pd.to_datetime(df_add['Timestamp'])
    df_add['ts2'] = df_add.Timestamp.tolist()
    df_add.set_index('Timestamp', inplace=True)

    # resample ints
    df_me = df_add[['capacity_usd', 'used_usd']].resample(self.freq_end, label='right').sum()

    # resample dates
    df_me['dt_start'] = df_add['ts2'].resample(self.freq_end, label='right').min()
    df_me['dt_end'] = df_add['ts2'].resample(self.freq_end, label='right').max()

    # dummy column showing 1 for the current instance, ie where there is any capacity
    # df_me['count_analyzed'] = 1
    df_me['count_analyzed'] = (df_me.capacity_usd > 0).astype(int)

    # append region
    #df_me['region'] = set([context_ec2['ec2_dict']['Region'])
    df_me['regions_set'] = df_me.apply(lambda row: frozenset([context_ec2['ec2_dict']['Region']]), axis=1)

    # cast all to int for simplicity
    for fx in ['capacity_usd', 'used_usd']:
      df_me[fx] = df_me[fx].fillna(value=0)
      df_me[fx] = df_me[fx].astype(int)

    # Add dataframes ints
    # Using the "+" operator will just fill missing indeces with NaN
    # https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.add.html
    add_cols = ['capacity_usd', 'used_usd', 'count_analyzed']
    df_sub1 = self.df_bins[add_cols]
    df_sub2 = df_me[add_cols]
    df_sub1 = df_sub1.add(df_sub2, fill_value=0)
    self.df_bins[add_cols] = df_sub1

    # bug in pandas.DataFrame.add function: it converts the int to float 
    # This is despite the dtypes of df_me and self.df_bins being int
    # and the fill_value being int
    # Probably due to missing index values feeding in "na" and later internally replacing the na with 0
    # TODO file issue and/or PR?
    for fx in ['capacity_usd', 'used_usd', 'count_analyzed']:
      self.df_bins[fx] = self.df_bins[fx].astype(int)

    # add the region sets
    self.df_bins['regions_set'] = pd_series_frozenset_union(self.df_bins['regions_set'], df_me['regions_set'])

    # add the start/end dates
    self.df_bins['dt_start'] = pd.concat([self.df_bins.dt_start, df_me.dt_start], axis=1).min(axis=1)
    self.df_bins['dt_end'  ] = pd.concat([self.df_bins.dt_end,   df_me.dt_end  ], axis=1).max(axis=1)

    # done
    return context_ec2

  def after_all(self, context_all):
    # add col for utilization in percentage
    import numpy as np
    def calc_usedPct(row):
      if row.capacity_usd==0: return 0
      o = row.used_usd / row.capacity_usd * 100
      return int(o)

    self.df_bins['used_pct'] = self.df_bins.apply(calc_usedPct, axis=1)

    # add column for regions as string
    self.df_bins['regions_str'] = self.df_bins['regions_set'].apply(lambda x: "0" if len(x)==0 else "%i (%s)"%(len(x), l2s(x)))

    # cases where dt_start > dt_end are those where there was no data and the initialization remained
    # so overwrite with na
    self.df_bins['dt_start'] = self.df_bins.apply(lambda row: np.nan if row.count_analyzed==0 else row.dt_start, axis=1)
    self.df_bins['dt_end']   = self.df_bins.apply(lambda row: np.nan if row.count_analyzed==0 else row.dt_end  , axis=1)

    # convert the dt_{start,end} back to dates again, given the nans
    for fx in ['dt_start', 'dt_end']: self.df_bins[fx] = pd.to_datetime(self.df_bins[fx])

    # Bugfix for cloudwatch:
    # When 90>=ndays>=64, cloudwatchman/metric.get_statistics returns data with max Timestamp on mainmanager.EndTime
    # Otherwise, the data max Timestamp is EndTime - 1 day
    # Here, get around this problem by incrementing by 1 day (or just set to mainmanager.EndTime)
    # This was tested on 2019-12-10 10:00 am UTC, and the last date was Dec 9 for ndays<64 and Dec 10 for ndays>=64
    if pd.notnull(self.df_bins['dt_end'].iloc[-1]):
      dt_max = context_all['mainManager'].EndTime.date()
      import datetime as dt
      dt_lastp1 = self.df_bins.dt_end.iloc[-1].date() + dt.timedelta(days=1)
      self.df_bins.iloc[-1, self.df_bins.columns=='dt_end'] = min(dt_max, dt_lastp1)

    # inject result for reporter access
    context_all['df_bins'] = self.df_bins
    return context_all


from isitfit.cost.base_reporter import ReporterBase

class ReporterAnalyzeEc2(ReporterBase):

  def postprocess(self, context_all):
    # unpack
    self.analyzer = context_all['analyzer']
    n_ec2_total, self.mm, n_ec2_analysed, region_include = context_all['n_ec2_total'], context_all['mainManager'], context_all['n_ec2_analysed'], context_all['region_include']

    # proceed
    cwau_val = 0
    if self.analyzer.sum_capacity!=0:
      cwau_val = self.analyzer.sum_used/self.analyzer.sum_capacity*100

    cwau_color = 'yellow'
    if cwau_val >= 70:
      cwau_color = 'green'
    elif cwau_val <= 30:
      cwau_color = 'red'

    dt_start = self.mm.StartTime.strftime("%Y-%m-%d")
    dt_end   = self.mm.EndTime.strftime("%Y-%m-%d")

    ri_max = 3
    ri_ell = "" if len(region_include)<=ri_max else "..."
    ri_str = ", ".join(region_include[:ri_max])+ri_ell
    
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
             'value': "%i (%s)"%(len(region_include), ri_str)
            },
            {'color': '',
             'label': "EC2 machines (total)",
             'value': "%i"%n_ec2_total
            },
            {'color': '',
             'label': "EC2 machines (analyzed)",
             'value': "%i"%n_ec2_analysed
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

    # save in context for aggregator
    context_all['table'] = self.table

    # done
    return context_all


  def display(self, context_all):
    def get_row(row):
        def get_cell(i):
          retc = row[i] if not row['color'] else colored(row[i], row['color'])
          return retc
        
        retr = [get_cell('label'), get_cell('value')]
        return retr

    dis_tab = [get_row(row) for row in self.table]

    # logger.info("Summary:")
    import click
    click.echo("Cost-Weighted Average Utilization (CWAU) of the AWS EC2 account:")
    click.echo("")
    click.echo(tabulate(dis_tab, headers=['Field', 'Value']))
    click.echo("")
    click.echo("For reference:")
    click.echo(colored("* CWAU >= 70% is well optimized", 'green'))
    click.echo(colored("* CWAU <= 30% is underused", 'red'))

    return context_all


  def email(self, context_all):
      """
      ctx - click context
      """
      context_2 = {}
      context_2['emailTo'] = context_all['emailTo']
      context_2['click_ctx'] = context_all['click_ctx']
      context_2['dataType'] = 'cost analyze' # ec2, not redshift
      context_2['dataVal'] = {'table': self.table}
      super().email(context_2)

      return context_all





def pipeline_factory(ctx, filter_tags, save_details):
    # moved these imports from outside the function to inside it so that `isitfit --version` wouldn't take 5 seconds due to the loading
    from isitfit.cost.mainManager import MainManager
    from isitfit.cost.cloudtrail_ec2type import CloudtrailCached
    from isitfit.cost.cacheManager import RedisPandas as RedisPandasCacheManager
    from isitfit.cost.datadogManager import DatadogCached
    from isitfit.cost.ec2_common import Ec2TagFilter
    from isitfit.cost.cloudwatchman import CloudwatchEc2
    from isitfit.cost.catalog_ec2 import Ec2Catalog
    from isitfit.cost.ec2_common import Ec2Common

    from isitfit.tqdmman import TqdmL2Verbose
    tqdml2_obj = TqdmL2Verbose(ctx)

    share_email = ctx.obj.get('share_email', None)
    ul = CalculatorAnalyzeEc2(ctx, save_details)

    # manager of redis-pandas caching
    cache_man = RedisPandasCacheManager()

    ddg = DatadogCached(cache_man)
    ddg.set_ndays(ctx.obj['ndays'])

    etf = Ec2TagFilter(filter_tags)

    cloudwatchman = CloudwatchEc2(cache_man)
    cloudwatchman.set_ndays(ctx.obj['ndays'])

    ra = ReporterAnalyzeEc2()

    mm = MainManager("EC2 cost analyze", ctx)
    mm.set_ndays(ctx.obj['ndays'])

    ec2_cat = Ec2Catalog()
    ec2_common = Ec2Common()
    ec2_it = Ec2Iterator(ctx.obj['filter_region'], tqdml2_obj)

    # boto3 cloudtrail data
    cloudtrail_manager = CloudtrailCached(mm.EndTime, cache_man, tqdml2_obj)

    # update dict and return it
    # https://stackoverflow.com/a/1453013/4126114
    inject_email_in_context = lambda context_all: dict({'emailTo': share_email}, **context_all)
    inject_analyzer = lambda context_all: dict({'analyzer': ul}, **context_all)

    # binning
    bcs = BinCapUsed()

    # utilization listeners
    mm.set_iterator(ec2_it)
    mm.add_listener('pre', cache_man.handle_pre)
    mm.add_listener('pre', cloudtrail_manager.init_data)
    mm.add_listener('pre', ec2_cat.handle_pre)
    mm.add_listener('pre', ul.handle_pre)
    mm.add_listener('pre', bcs.handle_pre)
    mm.add_listener('ec2', etf.per_ec2)
    mm.add_listener('ec2', cloudwatchman.per_ec2)
    mm.add_listener('ec2', cloudtrail_manager.single)
    mm.add_listener('ec2', ec2_common._handle_ec2obj)
    mm.add_listener('ec2', ddg.per_ec2)
    mm.add_listener('ec2', ul.per_ec2)
    mm.add_listener('ec2', bcs.per_ec2)
    mm.add_listener('all', ec2_common.after_all)
    mm.add_listener('all', ul.after_all)
    mm.add_listener('all', inject_analyzer)
    mm.add_listener('all', ra.postprocess)
    mm.add_listener('all', bcs.after_all)
    #mm.add_listener('all', ra.display)
    #mm.add_listener('all', inject_email_in_context)
    #mm.add_listener('all', ra.email)

    return mm


