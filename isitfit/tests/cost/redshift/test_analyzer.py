from isitfit.cost.redshift.analyzer import AnalyzerBase, AnalyzerAnalyze, AnalyzerOptimize


def test_redshiftPricingDict():
  from isitfit.cost.redshift.analyzer import redshiftPricing_dict
  assert len(redshiftPricing_dict.keys()) > 0



class TestAnalyzerBase:
  def test_init(self):
    ra = AnalyzerBase()
    assert True # no exception


  def test_fetchCount_zero(self):
    class MockIter:
      def iterate_core(self, just_counting, display_tqdm):
        return []

    # prepare
    mi = MockIter()
    ra = AnalyzerBase()
    ra.set_iterator(mi)

    # run and test
    ra.count()
    assert ra.n_rc_total == 0


  def test_fetchCount_one(self):
    class MockIter:
      def iterate_core(self, just_counting, display_tqdm):
        yield 1

    # prepare
    mi = MockIter()
    ra = AnalyzerBase()
    ra.set_iterator(mi)

    # run and test
    ra.count()
    assert ra.n_rc_total == 1


class TestAnalyzerAnalyze:

  def test_fetch(self):
    import pandas as pd
    import datetime as dt
    import pytz
    dt_now_d = dt.datetime.utcnow().replace(tzinfo=pytz.utc)
    ex_iter = [
      ({'ClusterIdentifier': 'abc', 'NodeType': 'dc2.large', 'NumberOfNodes': 3, 'ClusterCreateTime': dt_now_d, 'Region': 'bla'},
        pd.DataFrame([{'Average': 1, 'Timestamp': dt_now_d}]),
      ),
    ]
    class MockIter:
      service_description = 'test iterator'
      def __iter__(self):
        for i in ex_iter: yield i

    # prepare
    mi = MockIter()
    ra = AnalyzerAnalyze()
    ra.set_iterator(mi)
    ra.n_rc_total = 1

    # run and test
    ra.fetch()
    assert ra.analyze_df.shape[0] == 1


  def test_calculate(self):
    import pandas as pd

    ra = AnalyzerAnalyze()
    ra.analyze_df = pd.DataFrame([
      {'CostUsed': 1, 'CostBilled': 100, 'Region': 'bla'}
    ])
    ra.calculate()
    assert ra.cwau_percent == 1


class TestAnalyzerOptimize:

  def test_fetch(self):
    import pandas as pd
    ex_iter = [
      ( {'ClusterIdentifier': 'def', 'NodeType': 'dc2.large', 'NumberOfNodes': 3, 'Region': 'bla'},
        pd.DataFrame([{'Maximum': 1, 'Minimum': 1}]),
      ),
    ]
    class MockIter:
      service_description = 'test iterator'
      def __iter__(self):
        for i in ex_iter: yield i

    # prepare
    mi = MockIter()
    ra = AnalyzerOptimize()
    ra.set_iterator(mi)
    ra.n_rc_total = len(ex_iter)

    # run and test
    ra.fetch()
    assert ra.analyze_df.shape[0] == 1


  def test_calculate(self):
    import pandas as pd

    ra = AnalyzerOptimize()
    ra.analyze_df = pd.DataFrame([
      {'CpuMaxMax': 90, 'CpuMinMin': 80, 'Cost': 1, 'NumberOfNodes': 3},
      {'CpuMaxMax': 50, 'CpuMinMin':  1, 'Cost': 1, 'NumberOfNodes': 3},
    ])
    ra.calculate()
    assert ra.analyze_df.classification.tolist() == ['Overused', 'Normal']
