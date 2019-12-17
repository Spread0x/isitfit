from isitfit.cost.redshift_analyze import ReporterAnalyze
from isitfit.cost.base_reporter import ReporterBase
from isitfit.cost.redshift_optimize import ReporterOptimize


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
      regions_n = 1
      cost_billed = 1
      cost_used = 1

    rb = ReporterAnalyze()
    rb.postprocess({'analyzer': MockAnalyzer, 'mainManager': MockMm, 'n_ec2_total': 1, 'n_rc_analysed': 0})
    assert rb.table is not None



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


  def test_email(self, mocker):
    # assume user is not accepting to share by email, since will be prompted
    mockee = 'click.confirm'
    mocker.patch(mockee, side_effect=lambda x: False)
    #mockee = 'click.prompt'
    #mocker.patch(mockee, side_effect=lambda x: 'whatever')

    import pytest
    rb = ReporterOptimize()
    context_all = rb.email({'emailTo': []})
    assert True # assert no exceptions. The above .email will just return silently without doing anything since it is not implemented
