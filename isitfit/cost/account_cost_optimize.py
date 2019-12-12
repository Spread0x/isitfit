from isitfit.utils import logger

from isitfit.cost.base_reporter import ReporterBase
class ServiceReporter(ReporterBase):
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
      return context_all

    import pandas as pd
    self.table_c = pd.concat(t_all, axis=0, sort=False)

    # order columns
    # self.table_c.set_index([], inplace=True) # do not set index since display_df ignores the index ATM
    cols_theo = ['service', 'region', 'resource_id', 'resource_size1', 'resource_size2', 'classification_1', 'classification_2', 'cost_3m', 'recommended_size1', 'savings', 'tags']
    cols_all = [x for x in cols_theo if x in self.table_c.columns]
    self.table_c = self.table_c[cols_all]

    # group by for summary
    # TODO
    #self.table_a = self.table_c.groupby(['service', 'region'])

    return context_all


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
    # ATM just using the individual service reports
    import click

    if 'df_sort' not in self.table_d['ec2']:
      click.secho("No optimizations from EC2", fg='red')
    else:
      # copy from ec2_optimize.Reporter.display
      sum_val = self.table_d['ec2']['sum_val']
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

    if 'analyzer' not in self.table_d['redshift'].keys():
      click.secho("No optimizations from redshift", fg='red')
    elif self.table_d['redshift']['analyzer'].analyze_df.shape[0]==0:
      click.secho("No optimizations from redshift", fg='red')

    if self.table_c is None:
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
    return context_all



def pipeline_factory(mm_eco, mm_rco, ctx):
    from isitfit.cost.mainManager import RunnerAccount
    mm_all = RunnerAccount("AWS cost optimize (EC2, Redshift) in all regions", ctx)

    from .account_cost_analyze import ServiceIterator, ServiceCalculatorGet
    iterator = ServiceIterator(mm_eco, mm_rco)
    mm_all.set_iterator(iterator)

    calculator_get = ServiceCalculatorGet()
    mm_all.add_listener('ec2', calculator_get.per_service)

    reporter = ServiceReporter()
    mm_all.add_listener('ec2', reporter.per_service_save)
    mm_all.add_listener('all', reporter.concat)
    #mm_all.add_listener('all', reporter.display)
    mm_all.add_listener('all', reporter.display2)

    # done
    return mm_all
