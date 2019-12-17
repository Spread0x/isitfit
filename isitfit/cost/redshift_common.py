# redshift pricing as of 2019-11-12 in USD per hour, on-demand, ohio
# https://aws.amazon.com/redshift/pricing/
from isitfit.cost.catalog_redshift import redshiftPricing_dict



from isitfit.cost.base_iterator import BaseIterator
class RedshiftPerformanceIterator(BaseIterator):
  service_name = 'redshift'
  service_description = 'Redshift clusters'
  paginator_name = 'describe_clusters'
  paginator_entryJmespath = 'Clusters[]'
  paginator_exception = 'InvalidClientTokenId'
  entry_keyId = 'ClusterIdentifier'
  entry_keyCreated = 'ClusterCreateTime'




# AWS_DEFAULT_REGION=us-east-2 python3 -m isitfit.cost.test_redshift
# Related
# https://docs.datadoghq.com/integrations/amazon_redshift/
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/redshift.html#Redshift.Paginator.DescribeClusters

import pandas as pd
from isitfit.cost.metrics_cloudwatch import NoCloudwatchException



def tagsContain(f_tn, ec2_dict):
  """
  Similar to isitfit.cost.ec2_common.tagsContain
  """
  if ec2_dict['Tags'] is None: return False
  if len(ec2_dict['Tags']): return False

  for t in ec2_dict['Tags']:
    for k in ['Key', 'Value']:
      if f_tn in t[k].lower():
        return True
  
  return False


class RedshiftTagFilter:
  """
  Similar to isitfit.cost.ec2_common.Ec2TagFilter
  """
  def __init__(self, filter_tags):
    self.filter_tags = filter_tags

  def per_cluster(self, context_cluster):
    # if filters requested, check that this instance passes

    # set in context for the sake of filtering the taglist in redshift_optimize.Calculator.per_ec2
    context_cluster['filter_tags'] = self.filter_tags

    if self.filter_tags is None:
      # to continue with other listeners
      return context_cluster

    f_tn = self.filter_tags.lower()
    passesFilter = tagsContain(f_tn, context_cluster['ec2_dict'])

    if not passesFilter:
      # break other listeners
      return None

    # otherwise continue
    return context_cluster



class CalculatorBaseRedshift:


  def __init__(self):
    # define the list in the constructor because if I define it as a class member above,
    # then it gets reused between instantiations of derived classes
    self.analyze_list = []
    self.analyze_df = None


  def per_ec2(self, context_ec2):
      rc_describe_entry = context_ec2['ec2_dict']

      # for types not yet in pricing dictionary above
      rc_type = rc_describe_entry['NodeType']
      if rc_type not in redshiftPricing_dict.keys():
        raise NoCloudwatchException

      return context_ec2


  def after_all(self, context_all):
    # To be used by derived class *after* its own implementation

    # gather into a single dataframe
    self.analyze_df = pd.DataFrame(self.analyze_list)

    # update number of analyzed clusters
    context_all['n_rc_analysed'] = self.analyze_df.shape[0]

    # Edit 2019-11-20 no need to through exception here
    # This way, the code can proceed to show a report, and possibly proceed to other services than redshift
    #if context_all['n_rc_analysed']==0:
    #  from isitfit.cli.click_descendents import IsitfitCliError
    #  raise IsitfitCliError("No redshift clusters analyzed", context_all['click_ctx'])

    return context_all


  def calculate(self, context_all):
    raise Exception("To be implemented by derived class")







# Related
# https://docs.datadoghq.com/integrations/amazon_redshift/
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/redshift.html#Redshift.Paginator.DescribeClusters

import click

from isitfit.utils import logger



def redshift_cost_core(ra, rr, share_email, filter_region, ctx, filter_tags):
    """
    ra - Analyzer
    rr - Reporter
    """

    # data layer
    from isitfit.tqdmman import TqdmL2Verbose
    tqdmman = TqdmL2Verbose(ctx)

    ri = RedshiftPerformanceIterator(filter_region, tqdmman)

    # pipeline
    from isitfit.cost.mainManager import MainManager
    from isitfit.cost.cacheManager import RedisPandas as RedisPandasCacheManager
    from isitfit.cost.metrics_cloudwatch import CwRedshiftListener
    from isitfit.cost.ec2_common import Ec2Common
    from isitfit.cost.cloudtrail_ec2type import CloudtrailCached

    mm = MainManager("Redshift cost analyze or optimize", ctx)
    mm.set_ndays(ctx.obj['ndays'])

    cache_man = RedisPandasCacheManager()

    # manager of cloudwatch
    cwman = CwRedshiftListener(cache_man)
    cwman.set_ndays(ctx.obj['ndays'])

    # common stuff
    ec2_common = Ec2Common()

    # boto3 cloudtrail data
    # FIXME note that if two pipelines are run, one for ec2 and one for redshift, then this Object fetches the same data twice
    # because the base class behind it does both ec2+redshift at once
    # in the init_data phase
    cloudtrail_manager = CloudtrailCached(mm.EndTime, cache_man, tqdmman)

    # update dict and return it
    # https://stackoverflow.com/a/1453013/4126114
    inject_analyzer = lambda context_all: dict({'analyzer': ra}, **context_all)

    # binning
    do_binning = False
    ra_name = type(ra).__name__
    if ra_name == 'CalculatorOptimizeRedshift':
      do_binning = False
    elif ra_name == 'CalculatorAnalyzeRedshift':
      do_binning = True
    else:
      raise Exception("Invalid calculator class passed: %s"%ra_name)

    if do_binning:
      from isitfit.cost.ec2_analyze import BinCapUsed
      bcs = BinCapUsed()
      bcs.context_key = 'df_single'

    # setup pipeline
    mm.set_iterator(ri)
    mm.add_listener('pre', cache_man.handle_pre)
    mm.add_listener('pre', cloudtrail_manager.init_data)

    if do_binning:
      mm.add_listener('pre', bcs.handle_pre)

    rtf = RedshiftTagFilter(filter_tags)
    mm.add_listener('ec2', rtf.per_cluster)

    mm.add_listener('ec2', cwman.per_ec2)
    mm.add_listener('ec2', cloudtrail_manager.single)
    mm.add_listener('ec2', ra.per_ec2)

    if do_binning:
      mm.add_listener('ec2', bcs.per_ec2)

    mm.add_listener('all', ec2_common.after_all) # just show IDs missing cloudwatch/cloudtrail
    mm.add_listener('all', ra.after_all)
    mm.add_listener('all', ra.calculate)
    mm.add_listener('all', inject_analyzer)
    mm.add_listener('all', rr.postprocess)

    if do_binning:
      mm.add_listener('all', bcs.after_all)

    #inject_email_in_context = lambda context_all: dict({'emailTo': share_email}, **context_all)
    #mm.add_listener('all', rr.display)
    #mm.add_listener('all', inject_email_in_context)
    #mm.add_listener('all', rr.email)

    return mm



