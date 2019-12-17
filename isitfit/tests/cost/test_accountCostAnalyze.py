from isitfit.cost.account_cost_analyze import ServiceReporterBinned

class TestServiceReporterBinned:
  # pytest isitfit/tests/cost/redshift/test_reporter.py::TestReporterAnalyze::test_email
  def test_email(self, mocker):
    mockee = 'isitfit.emailMan.EmailMan'
    mocker.patch(mockee, autospec=True)

    mockee = 'isitfit.cost.base_reporter.ReporterBase.email'
    #mockee = 'isitfit.cost.account_cost_analyze.ReporterBase'
    # mocker.patch(mockee, autospec=True)
    mocker.patch(mockee, side_effect=lambda x: None)


    class MockClickCtx:
      obj = {
        'aws_profile': 'bla',
        'filter_region': None
      }

    rb = ServiceReporterBinned()
    rb.emailTo = []
    import pandas as pd
    context_all = {'dfbin_p': pd.DataFrame(), 'click_ctx': MockClickCtx()}
    rb.email(context_all)
    assert True # no exception


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

    rb = ServiceReporterBinned()
    context_all = {
      'dfbin_p': []
    }
    rb.display(context_all)
    assert True # no exception

