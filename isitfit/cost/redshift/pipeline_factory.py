

def redshift_cost_optimize(filter_region, ctx):
  # This is a factory method, so it doesn't make sense to display "Analyzing bla" if actually "foo" is analyzed first
  #logger.info("Optimizing redshift clusters")

  from .calculator import CalculatorOptimizeRedshift
  from .reporter import ReporterOptimize
  ra = CalculatorOptimizeRedshift()
  rr = ReporterOptimize()
  mm = redshift_cost_core(ra, rr, None, filter_region, ctx)

  # listener that was outed in the analyze step by the service aggregator
  # mm.add_listener('all', rr.display)

  return mm
