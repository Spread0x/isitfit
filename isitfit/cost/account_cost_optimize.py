from isitfit.cost.redshift.reporter import ReporterBase
class ServiceReporter(ReporterBase):
  def __init__(self):
    self.table_d = {'ec2': {}, 'redshift': {}}

  def per_service_save(self, context_service):
    service_name = context_service['ec2_id']
    context_all = context_service['context_all']
    if context_all is None: return context_service

    if service_name=='ec2':
      self.table_d['ec2']['df_sort'] = context_all['df_sort']
      self.table_d['ec2']['sum_val'] = context_all['sum_val']
      self.table_d['ec2']['csv_fn_final'] = context_all['csv_fn_final']
      self.table_d['ec2']['analyzer'] = context_all['analyzer']

    elif service_name=='redshift':
      # self.table_d['redshift']['analyze_df'] = context_all['analyzer'].analyze_df
      self.table_d['redshift']['analyzer'] = context_all['analyzer']
      self.table_d['redshift']['csv_fn_final'] = context_all['csv_fn_final']

    else:
      raise Exception("Invalid service runner description: %s"%service_name)

    return context_service


  def display(self, context_all):
    # ATM just using the individual service reports
    from isitfit.cost.ec2.reporter import ReporterOptimizeEc2
    roe = ReporterOptimizeEc2()
    roe.df_sort = self.table_d['ec2']['df_sort']
    roe.sum_val = self.table_d['ec2']['sum_val']
    roe.csv_fn_final = self.table_d['ec2']['csv_fn_final']
    roe.analyzer = self.table_d['ec2']['analyzer']
    roe.display(context_all)

    from isitfit.cost.redshift.reporter import ReporterOptimize as ReporterOptimizeRedshift
    ror = ReporterOptimizeRedshift()
    ror.analyzer = self.table_d['redshift']['analyzer']
    ror.csv_fn_final = self.table_d['redshift']['csv_fn_final']
    ror.display(context_all)

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
    mm_all.add_listener('all', reporter.display)

    # done
    return mm_all
