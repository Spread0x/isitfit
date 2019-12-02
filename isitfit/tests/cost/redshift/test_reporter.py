from isitfit.cost.redshift_analyze import ReporterAnalyze
from isitfit.cost.base_reporter import ReporterBase
from isitfit.cost.redshift_optimize import ReporterOptimize


class TestReporterBase:
  def test_init(self):
    rb = ReporterBase()
    assert True

  def test_promptToEmailIfNotRequested(self):
    import click
    from click.testing import CliRunner

    class MyWrap:
      def dummyFac(self, emailIn, emailPrompt):
        self.emailOut = None

        @click.command()
        def dummyCmd():
          rb = ReporterBase()
          self.emailOut = rb._promptToEmailIfNotRequested(emailIn)

        # https://stackoverflow.com/q/38143366/4126114
        runner = CliRunner()
        result = runner.invoke(dummyCmd, input=emailPrompt)
        return self.emailOut

    mw = MyWrap()
    actual = mw.dummyFac(None, '\n')
    assert actual is None
    actual = mw.dummyFac(None, 'n\n')
    assert actual is None
    actual = mw.dummyFac(None, 'y\nshadi@abc.com')
    assert actual == ['shadi@abc.com']
    actual = mw.dummyFac(None, 'y\nbla\nshadi@abc.com')
    assert actual == ['shadi@abc.com']




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


  # pytest isitfit/tests/cost/redshift/test_reporter.py::TestReporterAnalyze::test_email
  def test_email(self, mocker):
    mockee = 'isitfit.emailMan.EmailMan'
    mocker.patch(mockee, autospec=True)

    # assume user is not accepting to share by email, since will be prompted
    mockee = 'click.confirm'
    mocker.patch(mockee, side_effect=lambda x: False)
    #mockee = 'click.prompt'
    #mocker.patch(mockee, side_effect=lambda x: 'whatever')

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
