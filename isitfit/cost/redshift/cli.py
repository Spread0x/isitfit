import logging
logger = logging.getLogger('isitfit')


def cost_core(ra, rr, share_email):
    """
    ra - Analyzer
    rr - Reporter
    """

    # data layer
    from .iterator import RedshiftPerformanceIterator
    ri = RedshiftPerformanceIterator()
    ra.set_iterator(ri)
    ra.count()
    if ra.n_rc_total==0:
      logger.warning("No redshift clusters found")
      return

    ra.fetch()
    if ra.n_rc_analysed==0:
      logger.warning("No redshift clusters analyzed")
      return

    ra.calculate()

    # display layer
    rr.set_analyzer(ra)
    rr.postprocess()
    rr.display()
    if share_email is not None:
      if len(share_email) > 0:
        rr.email(share_email)


def cost_analyze(share_email):
  logger.info("Analyzing redshift clusters")

  from .analyzer import AnalyzerAnalyze
  from .reporter import ReporterAnalyze
  ra = AnalyzerAnalyze()
  rr = ReporterAnalyze()
  cost_core(ra, rr, share_email)

def cost_optimize():
  logger.info("Optimizing redshift clusters")

  from .analyzer import AnalyzerOptimize
  from .reporter import ReporterOptimize
  ra = AnalyzerOptimize()
  rr = ReporterOptimize()
  cost_core(ra, rr, None)
