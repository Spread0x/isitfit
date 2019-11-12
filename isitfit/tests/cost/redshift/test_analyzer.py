from isitfit.cost.redshift.analyzer import Analyzer


def test_redshiftPricingDict():
  from isitfit.cost.redshift.analyzer import redshiftPricing_dict
  assert len(redshiftPricing_dict.keys()) > 0



class TestAnalyzer:
  def test_init(self):
    ra = Analyzer(None)
    assert True # no exception


  def test_fetchCount_zero(self):
    class MockIter:
      def iterate_core(self):
        return []

    # prepare
    mi = MockIter()
    ra = Analyzer(mi)

    # run and test
    ra.fetch_count()
    assert ra.n_rc_total == 0


  def test_fetchCount_one(self):
    class MockIter:
      def iterate_core(self):
        yield 1

    # prepare
    mi = MockIter()
    ra = Analyzer(mi)

    # run and test
    ra.fetch_count()
    assert ra.n_rc_total == 1


  def test_fetchPerformances(self):
    import pandas as pd
    ex_iter = [
      ({'ClusterIdentifier': 'abc', 'NodeType': 'dc2.large', 'NumberOfNodes': 3},
        pd.DataFrame([{'Maximum': 1, 'Minimum': 1}]),
      ),
    ]
    class MockIter:
      def __iter__(self):
        for i in ex_iter: yield i

    # prepare
    mi = MockIter()
    ra = Analyzer(mi)
    ra.n_rc_total = 1

    # run and test
    ra.fetch_performances()
    assert ra.analyze_df.shape[0] == 1


  def test_calculateCwau(self):
    import pandas as pd

    ra = Analyzer(None)
    ra.analyze_df = pd.DataFrame([
      {'CpuMaxMax': 1, 'Cost': 1, 'NumberOfNodes': 3}
    ])
    ra.calculate_cwau()
    assert ra.cwau_percent == 1


  def test_classify(self):
    import pandas as pd

    ra = Analyzer(None)
    ra.analyze_df = pd.DataFrame([
      {'CpuMaxMax': 90, 'CpuMinMin': 80, 'Cost': 1, 'NumberOfNodes': 3},
      {'CpuMaxMax': 50, 'CpuMinMin':  1, 'Cost': 1, 'NumberOfNodes': 3},
    ])
    ra.classify()
    assert ra.analyze_df.classification.tolist() == ['Overused', 'Normal']
