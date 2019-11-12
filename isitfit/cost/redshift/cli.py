import logging
logger = logging.getLogger('isitfit')


def cost_core(is_analyze, share_email):
    pre_word = "Analyzing" if is_analyze else "Optimizing"
    logger.info("%s redshift clusters"%pre_word)

    from .iterator import RedshiftPerformanceIterator
    from .analyzer import Analyzer
    from .reporter import ReporterAnalyze, ReporterOptimize

    # data layer
    ri = RedshiftPerformanceIterator()
    ra = Analyzer(ri)

    ra.fetch_count()
    if ra.n_rc_total==0:
      logger.warning("No redshift clusters found")
      return

    ra.fetch_performances()
    if ra.n_rc_analysed==0:
      logger.warning("No redshift clusters analyzed")
      return

    ra.calculate_cwau()

    if not is_analyze:
      ra.classify()

    # display layer
    rr = None
    if is_analyze:
      rr = ReporterAnalyze(ra)
    else:
      rr = ReporterOptimize(ra)

    rr.postprocess()
    rr.display()
    if share_email is not None:
      if len(share_email) > 0:
        rr.email(share_email)


def cost_analyze(share_email):
  cost_core(True, share_email)

def cost_optimize():
  cost_core(False, None)
