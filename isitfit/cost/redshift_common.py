# redshift pricing as of 2019-11-12 in USD per hour, on-demand, ohio
# https://aws.amazon.com/redshift/pricing/
redshiftPricing_dict = {
  'dc2.large': 0.25,
  'dc2.8xlarge': 4.80,
  'ds2.xlarge': 0.85,
  'ds2.8xlarge': 6.80,
  'dc1.large': 0.25,
  'dc1.8xlarge': 4.80,
}



from isitfit.cost.redshift.iterator import BaseIterator
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
from isitfit.cost.mainManager import NoCloudwatchException


# redshift pricing as of 2019-11-12 in USD per hour, on-demand, ohio
# https://aws.amazon.com/redshift/pricing/
from isitfit.cost.redshift_common import redshiftPricing_dict



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
    #  from isitfit.utils import IsitfitCliError
    #  raise IsitfitCliError("No redshift clusters analyzed", context_all['click_ctx'])

    return context_all


  def calculate(self, context_all):
    raise Exception("To be implemented by derived class")







# Related
# https://docs.datadoghq.com/integrations/amazon_redshift/
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/redshift.html#Redshift.Paginator.DescribeClusters

import click

import logging
logger = logging.getLogger('isitfit')


class ReporterBase:
  def postprocess(self, context_all):
    raise Exception("To be implemented by derived class")

  def display(self, context_all):
    raise Exception("To be implemented by derived class")

  def _promptToEmailIfNotRequested(self, emailTo):
    if emailTo is not None:
      if len(emailTo) > 0:
        # user already requested email
        return emailTo

    # prompt user if to email
    click.echo("")
    res_conf = click.confirm("Would you like to share the results to your email?")
    if not res_conf:
      return None

    #from isitfit.utils import IsitfitCliError

    # more quick validation
    # works with a@b.c but not a@b@c.d
    # https://stackoverflow.com/questions/8022530/how-to-check-for-valid-email-address#8022584
    import re
    EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")

    # prompt for email
    while True:
      res_prompt = click.prompt('Please enter a valid email address (leave blank to skip)', type=str)

      # check if blank
      if res_prompt=='':
        return None

      # quick validate
      # shortest email is: a@b.c
      # Longest email is: shadishadishadishadi@shadishadishadishadi.shadi
      if len(res_prompt) >= 5:
        if len(res_prompt) <= 50:
          if bool(EMAIL_REGEX.match(res_prompt)):
            return [res_prompt]

      # otherwise, invalid email
      logger.error("Invalid email address: %s"%res_prompt)


  def email(self, context_all):
      """
      ctx - click context
      """
      for fx in ['dataType', 'dataVal']:
        if not fx in context_all:
          raise Exception("Missing field from context: %s. This function should be implemented by the derived class"%fx)

      # unpack
      emailTo, ctx = context_all['emailTo'], context_all['click_ctx']

      # prompt user for email if not requested
      emailTo = self._promptToEmailIfNotRequested(emailTo)

      # check if email requested
      if emailTo is None:
          return context_all

      if len(emailTo)==0:
          return context_all

      from isitfit.emailMan import EmailMan
      em = EmailMan(
        dataType=context_all['dataType'], # ec2, not redshift
        dataVal=context_all['dataVal'],
        ctx=ctx
      )
      em.send(emailTo)

      return context_all











def redshift_cost_core(ra, rr, share_email, filter_region, ctx):
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
    from isitfit.cost.cloudwatchman import CloudwatchRedshift
    from isitfit.cost.ec2_common import Ec2Common
    from isitfit.cost.cloudtrail_ec2type import CloudtrailCached

    mm = MainManager("Redshift cost analyze or optimize", ctx)
    cache_man = RedisPandasCacheManager()

    # manager of cloudwatch
    cwman = CloudwatchRedshift(cache_man)

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

    # setup pipeline
    mm.set_iterator(ri)
    mm.add_listener('pre', cache_man.handle_pre)
    mm.add_listener('pre', cloudtrail_manager.init_data)
    mm.add_listener('ec2', cwman.per_ec2)
    mm.add_listener('ec2', cloudtrail_manager.single)
    mm.add_listener('ec2', ra.per_ec2)
    mm.add_listener('all', ec2_common.after_all) # just show IDs missing cloudwatch/cloudtrail
    mm.add_listener('all', ra.after_all)
    mm.add_listener('all', ra.calculate)
    mm.add_listener('all', inject_analyzer)
    mm.add_listener('all', rr.postprocess)

    #inject_email_in_context = lambda context_all: dict({'emailTo': share_email}, **context_all)
    #mm.add_listener('all', rr.display)
    #mm.add_listener('all', inject_email_in_context)
    #mm.add_listener('all', rr.email)

    return mm



