import logging
logger = logging.getLogger('isitfit')


def cost_core(ra, rr, share_email, filter_region):
    """
    ra - Analyzer
    rr - Reporter
    """

    # data layer
    from .iterator import RedshiftPerformanceIterator
    ri = RedshiftPerformanceIterator(filter_region=filter_region)

    # pipeline
    from isitfit.cost.mainManager import MainManager
    from isitfit.cost.cacheManager import RedisPandas as RedisPandasCacheManager
    from .cloudwatchman import CloudwatchRedshift
    from isitfit.cost.ec2.ec2Common import Ec2Common

    mm = MainManager(None) # use None for click context for now FIXME
    cache_man = RedisPandasCacheManager()

    # manager of cloudwatch
    cwman = CloudwatchRedshift(cache_man)

    # common stuff
    ec2_common = Ec2Common()

    # update dict and return it
    # https://stackoverflow.com/a/1453013/4126114
    inject_email_in_context = lambda context_all: dict({'emailTo': share_email}, **context_all)
    inject_analyzer = lambda context_all: dict({'analyzer': ra}, **context_all)

    # setup pipeline
    mm.set_iterator(ri)
    mm.add_listener('pre', cache_man.handle_pre)
    mm.add_listener('ec2', cwman.per_ec2)
    mm.add_listener('ec2', ra.per_ec2)
    mm.add_listener('all', ec2_common.after_all) # just show IDs missing cloudwatch/cloudtrail
    mm.add_listener('all', ra.after_all)
    mm.add_listener('all', ra.calculate)
    mm.add_listener('all', inject_analyzer)
    mm.add_listener('all', rr.postprocess)
    mm.add_listener('all', rr.display)
    mm.add_listener('all', inject_email_in_context)
    mm.add_listener('all', rr.email)

    # kickoff
    mm.get_ifi()


def cost_analyze(share_email, filter_region):
  logger.info("Analyzing redshift clusters")

  from .analyzer import AnalyzerAnalyze
  from .reporter import ReporterAnalyze
  ra = AnalyzerAnalyze()
  rr = ReporterAnalyze()
  cost_core(ra, rr, share_email, filter_region)


def cost_optimize(filter_region):
  logger.info("Optimizing redshift clusters")

  from .analyzer import AnalyzerOptimize
  from .reporter import ReporterOptimize
  ra = AnalyzerOptimize()
  rr = ReporterOptimize()
  cost_core(ra, rr, None, filter_region)
