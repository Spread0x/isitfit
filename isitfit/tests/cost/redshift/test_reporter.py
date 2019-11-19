from isitfit.cost.redshift.reporter import ReporterBase, ReporterAnalyze, ReporterOptimize

class TestReporterBase:
  def test_init(self):
    rb = ReporterBase()
    assert True


class TestReporterAnalyze:
  def test_postprocess(self):
    import datetime as dt
    dt_now = dt.datetime.utcnow()

    class MockMm:
      StartTime = dt_now
      EndTime = dt_now

    class MockAnalyzer:
      class MockIter:
        pass

      cwau_percent = 10
      rp_iter = MockIter
      n_rc_total = 0
      n_rc_analysed = 0
      regions_n = 1
      cost_billed = 1
      cost_used = 1

    rb = ReporterAnalyze()
    rb.postprocess({'analyzer': MockAnalyzer, 'mainManager': MockMm})
    assert rb.table is not None


  def test_display(self):
    import datetime as dt
    dt_now = dt.datetime.utcnow()

    class MockAnalyzer:
      class MockIter:
        rc_noData = []
      class MockCw:
        pass

      rp_iter = MockIter
      cwman = MockCw

    rb = ReporterAnalyze()
    rb.table = [
      {'color': '', 'label': 'bla', 'value': 'foo'}
    ]
    rb.analyzer = MockAnalyzer
    rb.display({})
    assert True # no exception


  def test_email(self, mocker):
    mockee = 'isitfit.emailMan.EmailMan'
    mocker.patch(mockee, autospec=True)
    rb = ReporterAnalyze()
    rb.table = []
    rb.email({'emailTo': [], 'click_ctx': None})
    assert True # no exception



class TestReporterOptimize:
  def test_postprocess(self):
    import pandas as pd
    class MockAnalyzer:
      analyze_df = pd.DataFrame([{'CpuMaxMax': 1, 'CpuMinMin': 1}])

    rb = ReporterOptimize()
    rb.postprocess({'analyzer': MockAnalyzer})
    assert True # no exception


  def test_display(self, mocker):
    mockee = 'isitfit.utils.display_df'
    mocker.patch(mockee, autospec=True)

    import pandas as pd
    class MockAnalyzer:
      analyze_df = pd.DataFrame([{'CpuMaxMax': 1, 'CpuMinMin': 1}])

    rb = ReporterOptimize()
    rb.csv_fn_final = 'bla.csv'
    rb.analyzer = MockAnalyzer
    rb.display({})
    assert True # no exception


  def test_email(self):
    import pytest
    with pytest.raises(Exception):
      rb = ReporterOptimize()
      rb.email({'emailTo': []})

