from isitfit.utils import logger

from isitfit.cost.base_reporter import ReporterBase

class ServiceAggregator:
  def __init__(self):
    self.table_d = {'ec2': {}, 'redshift': {}}
    self.table_c = None
    self.table_a = None

  def per_service_save(self, context_service):
    service_name = context_service['ec2_id']
    context_all = context_service['context_all']
    if context_all is None: return context_service

    if service_name=='ec2':
      self.table_d['ec2']['df_sort'] = context_all['df_sort']
      self.table_d['ec2']['sum_val'] = context_all['sum_val']
      # after migration from display to display2, no need for these
      # self.table_d['ec2']['csv_fn_final'] = context_all['csv_fn_final']
      # self.table_d['ec2']['analyzer'] = context_all['analyzer']

    elif service_name=='redshift':
      self.table_d['redshift']['analyzer'] = context_all['analyzer']
      # after migration from display to display2, no need for these
      # self.table_d['redshift']['analyze_df'] = context_all['analyzer'].analyze_df
      # self.table_d['redshift']['csv_fn_final'] = context_all['csv_fn_final']

    else:
      raise Exception("Invalid service runner description: %s"%service_name)

    return context_service


  def _concat_ec2(self):
    if 'df_sort' not in self.table_d['ec2']:
      return None

    if self.table_d['ec2']['df_sort'] is None:
      return None

    # get 2 dataframes
    t_ec2 = self.table_d['ec2']['df_sort'].copy()

    # add service column
    t_ec2['service'] = 'EC2'

    # rename columns to match
    t_ec2.rename(columns={'instance_id':'resource_id', 'instance_type':'resource_size1', 'recommended_type':'recommended_size1'}, inplace=True)

    # append columns that exist in redshift, but not in ec2
    t_ec2['resource_size2'] = None

    return t_ec2


  def _concat_redshift(self):
    if 'analyzer' not in self.table_d['redshift'].keys():
      return

    if self.table_d['redshift']['analyzer'].analyze_df.shape[0]==0:
      return

    # get 2 dataframes
    t_rsh = self.table_d['redshift']['analyzer'].analyze_df.copy()

    # add service column
    t_rsh['service'] = 'Redshift'

    # rename columns to match
    t_rsh.rename(columns={'Region':'region', 'ClusterIdentifier':'resource_id', 'NodeType':'resource_size1', 'NumberOfNodes':'resource_size2', 'classification':'classification_1'}, inplace=True)
    del t_rsh['CpuMaxMax']
    del t_rsh['CpuMinMin']

    return t_rsh


  def concat(self, context_all):
    # get 2 dataframes
    t_ec2 = self._concat_ec2()
    t_rsh = self._concat_redshift()

    # concatenate
    t_all = [t_ec2, t_rsh]
    t_all = [x for x in t_all if x is not None]

    if len(t_all)==0:
      context_all['table_c'] = None
      return context_all

    import pandas as pd
    self.table_c = pd.concat(t_all, axis=0, sort=False)

    # order columns
    # self.table_c.set_index([], inplace=True) # do not set index since display_df ignores the index ATM
    cols_theo = ['service', 'region', 'resource_id', 'resource_size1', 'resource_size2', 'classification_1', 'classification_2', 'cost_3m', 'recommended_size1', 'savings', 'tags']

    # the "if x in" part is needed because if there are no redshift recommendations, there would be no column resource_size2
    # Update 2019-12-26 no longer need this since adding resource_size2=None to ec2 results. Keeping it anyway for now
    cols_all = [x for x in cols_theo if x in self.table_c.columns]

    # actual ordering of columns
    self.table_c = self.table_c[cols_all]

    # group by for summary
    # TODO
    #self.table_a = self.table_c.groupby(['service', 'region'])

    # add a new dt_detected for all recommendations. Those which had a dt_detected generated earlier will have this overwritten later
    import datetime as dt
    import pytz
    self.table_c['dt_detected'] = dt.datetime.utcnow().replace(tzinfo=pytz.utc)

    # save to context
    context_all['table_c'] = self.table_c

    return context_all



class SqliteMan:
  def __init__(self, click_ctx):
    # get profile name (for per-profile sqlite databases)
    # Note, no need to do a per-ndays database, since a recommendation of "change size from S1 to S2" is the same whether it is based on 7 days or 90 days
    # profile_name = context_all['click_ctx'].obj['aws_profile']
    profile_name = click_ctx.obj['aws_profile']

    # settings for local sqlite database
    import sqlite3
    from isitfit.dotMan import DotMan
    import os
    self.db_path = os.path.join(DotMan().get_dotisitfit(), "db_cost_optimize_01-%s.sqlite"%profile_name)
    #self.db_exists = os.path.exists(self.db_path) # before the .connect below automatically creates the file
    self.db_conn = sqlite3.connect(self.db_path)


  def read_sqlite(self, context_pre):
    # No need since the read_sql_query below will fail if the database didnt already exist
    #if not self.db_exists:
    #  return context_pre

    import pandas as pd
    try:
      table_previous = pd.read_sql_query('select * from recommendations_previous', self.db_conn)
    #except sqlite3.OperationalError:
    except pd.io.sql.DatabaseError:
      return context_pre

    # un-encode the tags_json field
    import json
    table_previous['tags'] = table_previous.tags_json.apply(lambda x: json.loads(x))
    del table_previous['tags_json']

    # display
    reporter = ServiceReporter()
    reporter.display2({'table_c': table_previous})

    # prompt user if should re-calculate, will raise click.Abort if user answers No
    # https://click.palletsprojects.com/en/7.x/api/?highlight=click%20confirm#click.confirm
    from termcolor import colored
    import click
    click.confirm(colored("Do you want to recalculate?", "red"), default=False, abort=True)

    # do not return into context since the program flow is:
    # - either abort now
    # - or re-calculate table_c in the aggregator
    #context_pre['table_c'] = table_previous
    return context_pre


  def update_dtCreated(self, context_all):
    """
    Save results to sqlite database, so that recommendations can get a UID attached and get tracked between re-runs
    """
    table_current = context_all['table_c']
    if table_current is None:     return context_all
    #if table_current.shape[0]==0: return context_all

    # convert column "tags" to "tags_json" since it is a list, and sqlite doesn't support lists
    import json
    table_current['tags_json'] = table_current.tags.apply(lambda x: json.dumps(x))

    # columns that need to go to sqlite
    cols_sqlite = [
      'service', 'region', 'resource_id',
      'resource_size1', 'resource_size2', 'classification_1', 'classification_2',
      'cost_3m', # not needed in left join below, but needed for read_sqlite
      'recommended_size1',
      'savings', # not needed in left join below, but needed for read_sqlite
      # 'tags', # This is a list, which sqlite doesn't support, so use tags_json instead (json-encoded)
      'tags_json', # not needed in left join below, but needed for read_sqlite
      'dt_detected',
    ]
    # cols_sqlite = [x for x in cols_sqlite if x in table_current.columns] # Update 2019-12-26 no longer need this since adding resource_size2=None to ec2 results

    # make sure that the table recommendations_previous exists
    # (use trick to append a 0-row table)
    df_empty = table_current[cols_sqlite].iloc[0:0]
    assert df_empty.shape[0] == 0
    df_empty.to_sql('recommendations_previous', self.db_conn, if_exists='append', index=False)

    # insert current table of recommendations into db
    table_current[cols_sqlite].to_sql('recommendations_current', self.db_conn, if_exists='replace', index=False)

    # join on previously saved recommendations
    # Note: the table recommendations_previous = recommendations_current with the dt_detected being the 1st date on which it was generated
    # Also note that the result is just the current recommendations
    import pandas as pd
    sql = """
    select
      -- service + region + resource ID: unique over resource life, other fields changeable
      rc.service,
      rc.region,
      rc.resource_id,

      -- date this recommendation was created
      COALESCE(rp.dt_detected, rc.dt_detected) as dt_detected

    from recommendations_current as rc
    left join recommendations_previous as rp
       on rc.service           = rp.service
      and rc.region            = rp.region
      and rc.resource_id       = rp.resource_id
      and rc.resource_size1    = rp.resource_size1
      and coalesce(rc.resource_size2, 'na')    = coalesce(rp.resource_size2, 'na') -- field that is missing for ec2
      and rc.classification_1  = rp.classification_1
      and rc.classification_2  = rp.classification_2
      and rc.recommended_size1 = rp.recommended_size1
    """
    table_dated = pd.read_sql_query(sql=sql, con=self.db_conn)

    # merge back table_dated into table_current (to get the corrected dt_detected field)
    cols_exDate = [x for x in table_current.columns if x!='dt_detected']
    table_current = table_current[cols_exDate].merge(table_dated, how='left', on=['service', 'region', 'resource_id'])

    # save table with corrected dt_detected back into db
    # Note that I'm not sure how this plays out with the --n=1 option
    # Method 1: simple, but loses all recommendations instead of preserving them all
    #           i.e. if a recommendation set is missing a recommendation R1, then it is deleted
    table_current[cols_sqlite].to_sql('recommendations_previous', self.db_conn, if_exists='replace', index=False)

    # drop the tags_json field since not needed except for sqlite
    del table_current['tags_json']

    # update in context
    context_all['table_c'] = table_current

    # done
    return context_all


class ServiceReporter(ReporterBase):
  # commenting this out in favor of display2
  # def display(self, context_all):
  #   # ATM just using the individual service reports
  #   from isitfit.cost.ec2_optimize import ReporterOptimizeEc2
  #   roe = ReporterOptimizeEc2()
  #   if 'df_sort' not in self.table_d['ec2']:
  #     import click
  #     click.echo("No optimizations from EC2")
  #   else:
  #     roe.df_sort = self.table_d['ec2']['df_sort']
  #     roe.sum_val = self.table_d['ec2']['sum_val']
  #     roe.csv_fn_final = self.table_d['ec2']['csv_fn_final']
  #     roe.analyzer = self.table_d['ec2']['analyzer']
  #     roe.display(context_all)
  #
  #   from isitfit.cost.redshift_optimize import ReporterOptimize as ReporterOptimizeRedshift
  #   ror = ReporterOptimizeRedshift()
  #   if 'analyzer' not in self.table_d['redshift'].keys():
  #     import click
  #     click.echo("No optimizations from redshift")
  #   elif self.table_d['redshift']['analyzer'].analyze_df.shape[0]==0:
  #     import click
  #     click.echo("No optimizations from redshift")
  #   else:
  #     ror.analyzer = self.table_d['redshift']['analyzer']
  #     ror.csv_fn_final = self.table_d['redshift']['csv_fn_final']
  #     ror.display(context_all)
  #
  #   return context_all


  def display2(self, context_all):
    """
    Re-write of self.display to merge the 2 dataframes of EC2 and Redshift into one table
    """
    self.table_c = context_all['table_c']

    # ATM just using the individual service reports
    import click

    # if 'df_sort' not in self.table_d['ec2']:
    if self.table_c is None:
      click.secho("No optimizations from EC2", fg='red')
    elif 'EC2' not in self.table_c['service'].to_list():
      click.secho("No optimizations from EC2", fg='red')
    else:
      # copy from ec2_optimize.Reporter.display
      # sum_val = self.table_d['ec2']['sum_val']
      sum_val = self.table_c.savings.sum()
      if sum_val==0:
        # Update 2019-12-12 bring back the echo below (after having been commented out for a few days)
        click.secho("No optimizations from EC2", fg='red')
        #pass
      elif sum_val is None:
        # Update 2019-12-12 bring back the echo below (after having been commented out for a few days)
        click.secho("No optimizations from EC2", fg='red')
        #pass
      else:
        sum_comment = "extra cost" if sum_val>0 else "savings"
        sum_color = "red" if sum_val>0 else "green"
        click.secho("EC2 %s over the next 3 months: $ %0.0f"%(sum_comment, sum_val), fg=sum_color)

    # spacer
    click.echo("")

    #if 'analyzer' not in self.table_d['redshift'].keys():
    #  click.secho("No optimizations from redshift", fg='red')
    #elif self.table_d['redshift']['analyzer'].analyze_df.shape[0]==0:
    #  click.secho("No optimizations from redshift", fg='red')

    if self.table_c is None:
      click.secho("No optimizations from redshift", fg='red')
    elif 'Redshift' not in self.table_c['service'].to_list():
      click.secho("No optimizations from redshift", fg='red')

    if self.table_c is None:
      return context_all

    if self.table_c.shape[0]==0:
      return context_all

    # save concatenated table to CSV
    # copied from isitfit.cost.optimizationListener.storecsv...
    import tempfile
    from isitfit.dotMan import DotMan
    with tempfile.NamedTemporaryFile(prefix='isitfit-costOptimize-', suffix='.csv', delete=False, dir=DotMan().tempdir()) as csv_fh_final:
      click.secho("Saving final results to %s"%csv_fh_final.name, fg="cyan")
      self.table_c.to_csv(csv_fh_final.name, index=False)
      click.secho("Save complete", fg="cyan")

    # display concatenated table
    from isitfit.utils import display_df
    display_df(
      "Optimization summary",
      self.table_c,
      # self.table_a, # TODO
      csv_fh_final.name,
      self.table_c.shape,
      logger
    )

    # done
    return context_all



def pipeline_factory(mm_eco, mm_rco, ctx):
    from isitfit.cost.mainManager import RunnerAccount
    mm_all = RunnerAccount("AWS cost optimize (EC2, Redshift) in all regions", ctx)

    # add listener that checks the local sqlite database for a previous calculation
    # and display if available, then prompt user if desires to re-calculate
    # Note that if no desire to re-calculate, this raises an exception that bubbles up into get_ifi and aborts the pipeline early
    sqlite_man = SqliteMan(ctx)

    # Update 2019-12-27 will not display the database table ATM, in favor of using it in the interactive command
    # mm_all.add_listener('pre', sqlite_man.read_sqlite)

    # set up a pipeline that fetches fresh data
    from .account_cost_analyze import ServiceIterator, ServiceCalculatorGet
    iterator = ServiceIterator(mm_eco, mm_rco)
    mm_all.set_iterator(iterator)

    calculator_get = ServiceCalculatorGet()
    mm_all.add_listener('ec2', calculator_get.per_service)

    aggregator = ServiceAggregator()
    mm_all.add_listener('ec2', aggregator.per_service_save)
    mm_all.add_listener('all', aggregator.concat)

    mm_all.add_listener('all', sqlite_man.update_dtCreated)

    # whether reading from sqlite or fresh data, display
    reporter = ServiceReporter()
    #mm_all.add_listener('all', reporter.display)
    mm_all.add_listener('all', reporter.display2)

    # done
    return mm_all
