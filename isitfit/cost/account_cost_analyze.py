from isitfit.utils import logger



class ServiceIterator:
  """
  Similar to isitfit.cost.redshift.iterator.BaseIterator
  """
  service_description = "AWS EC2, Redshift"
  region_include = None
  def __init__(self, s_ec2, s_redshift):
    self.s_ec2 = s_ec2
    self.s_redshift = s_redshift

  def count(self):
    return 2

  def get_regionInclude(self):
    return None

  def __iter__(self):
    s_l = [ ('ec2',      self.s_ec2),
            ('redshift', self.s_redshift)
          ]
    for s_name, s_i in s_l:
      yield None, s_name, None, s_i



class ServiceCalculatorGet:
  def per_service(self, context_service):
    service_i = context_service['ec2_obj']

    # configure tqdm
    from isitfit.tqdmman import TqdmL2Verbose
    tqdml2_obj = TqdmL2Verbose(service_i.ctx)

    # run pipeline
    context_all = service_i.get_ifi(tqdml2_obj)
    context_service['context_all'] = context_all
    return context_service


class ServiceCalculatorSave:
  def __init__(self):
    self.table_d = {}

  def per_service(self, context_service):
    service_name = context_service['ec2_id']

    context_all = context_service['context_all']
    if context_all is None: return context_service

    table_single = context_all['table']
    table_single = {v['label']: v for v in table_single}
    self.table_d[service_name] = table_single

    return context_service

    

class ServiceCalculatorBinned:
  def __init__(self):
    self.dfbin_d = {}
    self.dfbin_p = None

  def per_service(self, context_service):
    service_name = context_service['ec2_id']

    context_all = context_service['context_all']
    if context_all is None: return context_service

    # get df_bin
    if 'df_bins' not in context_service['context_all']:
      return context_service

    # shortcut
    df_i = context_service['context_all']['df_bins']

    # timestamp index to regular column to convert to date
    # Update 2019-12-08 need to convert to string instead of date
    # because otherwise in --share-email
    # the shared email will show the UNIX integer timestamp in the column name
    # and the date cells
    df_i = df_i.reset_index()
    for fx in ['Timestamp', 'dt_start', 'dt_end']:
      # df_i[fx] = df_i[fx].dt.date
      df_i[fx] = df_i[fx].dt.strftime("%Y-%m-%d")

    df_i.set_index('Timestamp', inplace=True)

    # sort columns for later's after_all, and drop regions_set
    df_i = df_i[['dt_start', 'dt_end', 'regions_str', 'count_analyzed', 'capacity_usd', 'used_usd', 'used_pct']]
    
    # pretty-print dollar/percentage signs
    df_i['capacity_usd'] = df_i['capacity_usd'].apply(lambda x: "%0.0f $"%x)
    df_i['used_usd'    ] = df_i['used_usd'    ].apply(lambda x: "%0.0f $"%x)
    df_i['used_pct'    ] = df_i['used_pct'    ].apply(lambda x: "%0.0f %%"%x)

    
    # Replace code-friendly strings with human-friendly strings
    fm = {
      'dt_start': 'Start date',
      'dt_end': 'End date',
      'regions_str': 'Regions',
      'count_analyzed': 'Resources analyzed',
      'capacity_usd': 'Billed cost',
      'used_usd': 'Used cost',
      'used_pct': 'CWAU (Used/Billed)',
    }
    df_i.rename(columns=fm, inplace=True)

    # transpose to match format of one-column output
    df_i = df_i.transpose()

    # add service name, so that EC2 and Redshift don't get mixed up
    df_i['Service'] = service_name

    # save
    self.dfbin_d[service_name] = df_i

    return context_service


  def after_all(self, context_all):
    """
    concatenate the self.dfbin_d dict to pandas dataframe
    """
    dfbin_l = [v.reset_index() for k,v in self.dfbin_d.items()]
    if len(dfbin_l)==0:
      from isitfit.cli.click_descendents import IsitfitCliError
      raise IsitfitCliError("No data found")

    import pandas as pd
    self.dfbin_p = pd.concat(dfbin_l, axis=0)

    # rename the weird "Timestamp" column to "Field"
    self.dfbin_p.rename(columns={'index': 'Field'}, inplace=True)

    # set index
    self.dfbin_p.set_index(['Service', 'Field'], inplace=True)

    # save for later processing
    context_all['dfbin_p'] = self.dfbin_p

    # done
    return context_all



from isitfit.cost.base_reporter import ReporterBase

#class ServiceReporterTotals(ReporterBase):
#  def __init__(self):
#    self.table_merged = []
#
#  def postprocess(self, context_all):
#    # get first available start/end date
#    analyzer = context_all['analyzer']
#    date_source = analyzer.table_d.get('ec2', analyzer.table_d.get('redshift', None))
#    if date_source is None:
#      # no data for ec2 and redshift
#      return context_all
#
#    self.table_merged += [
#      {'color': '',
#       'label': "Start date",
#       'value':  date_source['Start date']['value'] # just take first
#      },
#      {'color': '',
#       'label': "End date",
#       'value': date_source['End date']['value'] # just take first
#      },
#    ]
#
#    # if no EC2:
#    if 'ec2' not in analyzer.table_d.keys():
#      self.table_merged.append(
#        {'color': '',
#         'label': "EC2 instances",
#         'value': "None found",
#        },
#      )
#    else:
#      self.table_merged += [
#        {'color': '',
#         'label': "EC2 Regions",
#         'value': analyzer.table_d['ec2']['Regions']['value'],
#        },
#        {'color': '',
#         'label': "EC2 machines (total)",
#         'value': analyzer.table_d['ec2']['EC2 machines (total)']['value'] # only 1 anyway
#        },
#        {'color': '',
#         'label': "EC2 machines (analyzed)",
#         'value': analyzer.table_d['ec2']['EC2 machines (analyzed)']['value'] # only 1 anyway
#        },
#        {'color': 'cyan',
#         'label': "EC2 Billed cost",
#         'value': analyzer.table_d['ec2']['Billed cost']['value']
#        },
#        {'color': 'cyan',
#         'label': "EC2 Used cost",
#         'value': analyzer.table_d['ec2']['Used cost']['value']
#        },
#        {'color': analyzer.table_d['ec2']['CWAU (Used/Billed)']['color'],
#         'label': "EC2 CWAU (Used/Billed)",
#         'value': analyzer.table_d['ec2']['CWAU (Used/Billed)']['value']
#        },
#      ]
#
#    # if no Redshift:
#    if 'redshift' not in analyzer.table_d.keys():
#      self.table_merged.append(
#        {'color': '',
#         'label': "Redshift clusters",
#         'value': "None found",
#        },
#      )
#    else:
#      self.table_merged += [
#        {'color': '',
#         'label': "Redshift Regions",
#         'value': analyzer.table_d['redshift']['Regions']['value']
#        },
#        {'color': '',
#         'label': "Redshift clusters (total)",
#         'value': analyzer.table_d['redshift']['Redshift clusters (total)']['value'] # only 1 anyway
#        },
#        {'color': '',
#         'label': "Redshift clusters (analyzed)",
#         'value': analyzer.table_d['redshift']['Redshift clusters (analyzed)']['value'] # only 1 anyway
#        },
#        {'color': 'cyan',
#         'label': "Redshift Billed cost",
#         'value': analyzer.table_d['redshift']['Billed cost']['value']
#        },
#        {'color': 'cyan',
#         'label': "Redshift Used cost",
#         'value': analyzer.table_d['redshift']['Used cost']['value']
#        },
#        {'color': analyzer.table_d['redshift']['CWAU (Used/Billed)']['color'],
#         'label': "Redshift CWAU (Used/Billed)",
#         'value': analyzer.table_d['redshift']['CWAU (Used/Billed)']['value']
#        },
#    ]
#
#    # done
#    return context_all
#
#  def display(self, context_all):
#    import click
#
#    if not self.table_merged:
#      click.echo("No resources found in AWS EC2, Redshift")
#      return context_all
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
#    dis_tab = [get_row(row) for row in self.table_merged]
#
#    # logger.info("Summary:")
#    from tabulate import tabulate
#    click.echo("Cost-Weighted Average Utilization (CWAU) of the AWS account:")
#    click.echo("")
#    click.echo(tabulate(dis_tab, headers=['Field', 'Value']))
#    click.echo("")
#    click.echo("For reference:")
#    click.echo(colored("* CWAU >= 70% is well optimized", 'green'))
#    click.echo(colored("* CWAU <= 30% is underused", 'red'))
#
#    return context_all
#
#  def email(self, context_all):
#      if self.emailTo is None: return context_all
#
#      context_2 = {}
#      context_2['emailTo'] = self.emailTo
#      context_2['click_ctx'] = context_all['click_ctx']
#      context_2['dataType'] = 'cost analyze' # redshift + ec2
#      context_2['dataVal'] = {'table': self.table_merged}
#      super().email(context_2)
#
#      return context_all



class ServiceReporterBinned(ReporterBase):
  def display(self, context_all):
    dfbin_p = context_all['dfbin_p']

    import click
    from termcolor import colored
    from tabulate import tabulate

    # logger.info("Summary:")
    click.echo("Cost-Weighted Average Utilization (CWAU) of the AWS account (EC2, Redshift):")
    click.echo("")
    click.echo(dfbin_p)
    click.echo("")
    click.echo("For reference:")
    click.echo(colored("* CWAU >= 70% is well optimized", 'green'))
    click.echo(colored("* CWAU <= 30% is underused", 'red'))
    click.echo("")

    return context_all


  def email(self, context_all):
      if self.emailTo is None: return context_all

      dfbin_p = context_all['dfbin_p']
      ctx = context_all['click_ctx']

      # FIXME pandas bug: to_json on dataframe with index yields unreadable json
      # i.e. pd.read_json(dfbin_p.to_json()) raises an exception
      # So need to reset_index first, and then set index again on the server-side
      # dfbin_s = dfbin_p.to_json()
      dfbin_s = dfbin_p.reset_index().to_json()

      context_2 = {}
      context_2['emailTo'] = self.emailTo
      context_2['click_ctx'] = context_all['click_ctx']
      context_2['dataType'] = 'cost analyze (binned)' # redshift + ec2
      context_2['dataVal'] = {
        'table': dfbin_s,
        'options': {
          'aws_profile': ctx.obj['aws_profile'],
          'filter_region': ctx.obj['filter_region'] or 'all'
        }
      }
      super().email(context_2)

      return context_all




def pipeline_factory(mm_eca, mm_rca, ctx, share_email):
    """
    Combines the 2 pipelines from EC2 and Redshift
    mm_eca - pipeline of EC2 cost analyze
    mm_rca - pipeline of Redshift cost analyze
    ctx - click context
    share_email - list of emails or None
    """
    from isitfit.cost.mainManager import RunnerAccount
    mm_all = RunnerAccount("AWS cost analyze (EC2, Redshift) in all regions", ctx)

    service_iterator = ServiceIterator(mm_eca, mm_rca)
    mm_all.set_iterator(service_iterator)

    service_calculator_get = ServiceCalculatorGet()
    mm_all.add_listener('ec2', service_calculator_get.per_service)

    service_calculator_save = ServiceCalculatorSave()
    mm_all.add_listener('ec2', service_calculator_save.per_service)

    service_calculator_binned = ServiceCalculatorBinned()
    mm_all.add_listener('ec2', service_calculator_binned.per_service)
    mm_all.add_listener('all', service_calculator_binned.after_all)

    # update dict and return it
    # https://stackoverflow.com/a/1453013/4126114
    # inject_analyzer = lambda context_all: dict({'analyzer': service_calculator_save}, **context_all)
    # inject_analyzer = lambda context_all: dict({'calculator_binned': service_calculator_binned}, **context_all)
    # mm_all.add_listener('all', inject_analyzer)
    # 
    # service_reporter = ServiceReporterTotals()
    # service_reporter.emailTo = share_email
    # mm_all.add_listener('all', service_reporter.postprocess)
    # mm_all.add_listener('all', service_reporter.display)
    # mm_all.add_listener('all', service_reporter.email)

    service_reporter = ServiceReporterBinned()
    service_reporter.emailTo = share_email
    mm_all.add_listener('all', service_reporter.display)
    mm_all.add_listener('all', service_reporter.email)

    # done
    return mm_all




