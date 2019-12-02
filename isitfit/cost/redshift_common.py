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




import logging
logger = logging.getLogger('isitfit')


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
    from isitfit.cost.redshift.cloudwatchman import CloudwatchRedshift
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



