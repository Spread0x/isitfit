import logging
logger = logging.getLogger('isitfit')


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



class ServiceCalculator:
  def __init__(self):
    self.table_d = {}

  def per_service(self, context_service):
    service_i = context_service['ec2_obj']
    service_name = context_service['ec2_id']

    # configure tqdm
    from isitfit.tqdmman import TqdmL2Verbose
    tqdml2_obj = TqdmL2Verbose(service_i.ctx)

    # run pipeline
    context_all = service_i.get_ifi(tqdml2_obj)

    if context_all is None: return context_service
    table_single = context_all['table']
    table_single = {v['label']: v for v in table_single}
    self.table_d[service_name] = table_single
    return context_service
    

from isitfit.cost.redshift.reporter import ReporterBase
class ServiceReporter(ReporterBase):
  def __init__(self):
    self.table_merged = []

  def postprocess(self, context_all):
    # get first available start/end date
    analyzer = context_all['analyzer']
    date_source = analyzer.table_d.get('ec2', analyzer.table_d.get('redshift', None))
    if date_source is None:
      # no data for ec2 and redshift
      return context_all

    self.table_merged += [
      {'color': '',
       'label': "Start date",
       'value':  date_source['Start date']['value'] # just take first
      },
      {'color': '',
       'label': "End date",
       'value': date_source['End date']['value'] # just take first
      },
    ]

    # if no EC2:
    if 'ec2' not in analyzer.table_d.keys():
      self.table_merged.append(
        {'color': '',
         'label': "EC2 instances",
         'value': "None found",
        },
      )
    else:
      self.table_merged += [
        {'color': '',
         'label': "EC2 Regions",
         'value': analyzer.table_d['ec2']['Regions']['value'],
        },
        {'color': '',
         'label': "EC2 machines (total)",
         'value': analyzer.table_d['ec2']['EC2 machines (total)']['value'] # only 1 anyway
        },
        {'color': '',
         'label': "EC2 machines (analyzed)",
         'value': analyzer.table_d['ec2']['EC2 machines (analyzed)']['value'] # only 1 anyway
        },
        {'color': 'cyan',
         'label': "EC2 Billed cost",
         'value': analyzer.table_d['ec2']['Billed cost']['value']
        },
        {'color': 'cyan',
         'label': "EC2 Used cost",
         'value': analyzer.table_d['ec2']['Used cost']['value']
        },
        {'color': analyzer.table_d['ec2']['CWAU (Used/Billed)']['color'],
         'label': "EC2 CWAU (Used/Billed)",
         'value': analyzer.table_d['ec2']['CWAU (Used/Billed)']['value']
        },
      ]

    # if no Redshift:
    if 'redshift' not in analyzer.table_d.keys():
      self.table_merged.append(
        {'color': '',
         'label': "Redshift clusters",
         'value': "None found",
        },
      )
    else:
      self.table_merged += [
        {'color': '',
         'label': "Redshift Regions",
         'value': analyzer.table_d['redshift']['Regions']['value']
        },
        {'color': '',
         'label': "Redshift clusters (total)",
         'value': analyzer.table_d['redshift']['Redshift clusters (total)']['value'] # only 1 anyway
        },
        {'color': '',
         'label': "Redshift clusters (analyzed)",
         'value': analyzer.table_d['redshift']['Redshift clusters (analyzed)']['value'] # only 1 anyway
        },
        {'color': 'cyan',
         'label': "Redshift Billed cost",
         'value': analyzer.table_d['redshift']['Billed cost']['value']
        },
        {'color': 'cyan',
         'label': "Redshift Used cost",
         'value': analyzer.table_d['redshift']['Used cost']['value']
        },
        {'color': analyzer.table_d['redshift']['CWAU (Used/Billed)']['color'],
         'label': "Redshift CWAU (Used/Billed)",
         'value': analyzer.table_d['redshift']['CWAU (Used/Billed)']['value']
        },
    ]

    # done
    return context_all

  def display(self, context_all):
    import click

    if not self.table_merged:
      click.echo("No resources found in AWS EC2, Redshift")
      return context_all

    # https://pypi.org/project/termcolor/
    from termcolor import colored

    def get_row(row):
        def get_cell(i):
          retc = row[i] if not row['color'] else colored(row[i], row['color'])
          return retc
        
        retr = [get_cell('label'), get_cell('value')]
        return retr

    dis_tab = [get_row(row) for row in self.table_merged]

    # logger.info("Summary:")
    from tabulate import tabulate
    click.echo("Cost-Weighted Average Utilization (CWAU) of the AWS account:")
    click.echo("")
    click.echo(tabulate(dis_tab, headers=['Field', 'Value']))
    click.echo("")
    click.echo("For reference:")
    click.echo(colored("* CWAU >= 70% is well optimized", 'green'))
    click.echo(colored("* CWAU <= 30% is underused", 'red'))

    return context_all

  def email(self, context_all):
      context_2 = {}
      context_2['emailTo'] = context_all['emailTo']
      context_2['click_ctx'] = context_all['click_ctx']
      context_2['dataType'] = 'cost analyze' # redshift + ec2
      context_2['dataVal'] = {'table': self.table_merged}
      super().email(context_2)

      return context_all


def service_cost_analyze(mm_eca, mm_rca, ctx, share_email):
    """
    Combines the 2 pipelines from EC2 and Redshift
    """
    from isitfit.cost.mainManager import RunnerAccount
    mm_all = RunnerAccount("AWS cost analyze (EC2, Redshift) in all regions", ctx)

    # from isitfit.cost.service import ServiceIterator, ServiceCalculator, ServiceReporter

    service_iterator = ServiceIterator(mm_eca, mm_rca)
    mm_all.set_iterator(service_iterator)

    service_calculator = ServiceCalculator()
    mm_all.add_listener('ec2', service_calculator.per_service)

    # update dict and return it
    # https://stackoverflow.com/a/1453013/4126114
    inject_analyzer = lambda context_all: dict({'analyzer': service_calculator}, **context_all)
    mm_all.add_listener('all', inject_analyzer)

    service_reporter = ServiceReporter()
    mm_all.add_listener('all', service_reporter.postprocess)

    mm_all.add_listener('all', service_reporter.display)

    # update dict and return it
    # https://stackoverflow.com/a/1453013/4126114
    inject_email_in_context = lambda context_all: dict({'emailTo': share_email}, **context_all)
    mm_all.add_listener('all', inject_email_in_context)

    mm_all.add_listener('all', service_reporter.email)

    # done
    return mm_all



def service_cost_optimize(mm_eco, mm_rco, ctx):
    # configure tqdm
    from isitfit.tqdmman import TqdmL2Quiet, TqdmL2Verbose
    tqdml2_ec2 = TqdmL2Verbose(ctx)
    tqdml2_redshift = TqdmL2Verbose(ctx)
    tqdml2_account = TqdmL2Quiet(ctx)

    # start download data and processing
    it_l = [
      (mm_eco, tqdml2_ec2,      "EC2"     ),
      (mm_rco, tqdml2_redshift, "Redshift"),
    ]
    it_w = tqdml2_account(it_l, total=len(it_l), desc="AWS EC2, Redshift cost optimize")
    for mm_i, tqdml2_i, desc_i in it_w:
      logger.info("Fetching history: %s..."%desc_i)
      mm_i.get_ifi(tqdml2_i)

