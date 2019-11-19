from isitfit.cost.redshift.analyzer import AnalyzerBase, AnalyzerAnalyze, AnalyzerOptimize
import datetime as dt
import pandas as pd
import pytz
dt_now_d = dt.datetime.utcnow().replace(tzinfo=pytz.utc)


def test_redshiftPricingDict():
  from isitfit.cost.redshift.analyzer import redshiftPricing_dict
  assert len(redshiftPricing_dict.keys()) > 0



class TestAnalyzerBase:
  def test_init(self):
    ra = AnalyzerBase()
    assert True # no exception


class TestAnalyzerAnalyze:

  def test_fetch(self, mocker):
    mockreturn = lambda *args, **kwargs: pd.DataFrame({'Timestamp': [], 'Average': []})
    mockee = 'isitfit.cost.redshift.cloudwatchman.CloudwatchRedshift.handle_main'
    mocker.patch(mockee, side_effect=mockreturn)

    import datetime as dt
    import pytz
    dt_now_d = dt.datetime.utcnow().replace(tzinfo=pytz.utc)
    ex_iter = [
      ({'ClusterIdentifier': 'abc', 'NodeType': 'dc2.large', 'NumberOfNodes': 3, 'ClusterCreateTime': dt_now_d, 'Region': 'bla'},
        #pd.DataFrame([{'Average': 1, 'Timestamp': dt_now_d}]),
        'def',
        dt_now_d
      ),
    ]

    # prepare
    ra = AnalyzerAnalyze()
    ra.analyze_list = ex_iter

    # run and test
    ra.after_all({'click_ctx': None})
    assert ra.analyze_df.shape[0] == 1


  def test_calculate(self):
    ra = AnalyzerAnalyze()
    ra.analyze_df = pd.DataFrame([
      {'CostUsed': 1, 'CostBilled': 100, 'Region': 'bla'}
    ])
    ra.calculate({})
    assert ra.cwau_percent == 1


class TestAnalyzerOptimize:

  def test_fetch(self, mocker):
    mockreturn = lambda *args, **kwargs: pd.DataFrame({'Timestamp': [], 'Average': [], 'Maximum': [], 'Minimum': []})
    mockee = 'isitfit.cost.redshift.cloudwatchman.CloudwatchRedshift.handle_main'
    mocker.patch(mockee, side_effect=mockreturn)

    ex_iter = [
      ( {'ClusterIdentifier': 'def', 'NodeType': 'dc2.large', 'NumberOfNodes': 3, 'Region': 'bla'},
        # pd.DataFrame([{'Maximum': 1, 'Minimum': 1}]),
        'def',
        dt_now_d
      ),
    ]

    # prepare
    ra = AnalyzerOptimize()
    ra.analyze_list = ex_iter

    # run and test
    ra.after_all({'click_ctx': None})
    assert ra.analyze_df.shape[0] == 1


  def test_calculate(self):
    ra = AnalyzerOptimize()
    ra.analyze_df = pd.DataFrame([
      {'CpuMaxMax': 90, 'CpuMinMin': 80, 'Cost': 1, 'NumberOfNodes': 3},
      {'CpuMaxMax': 50, 'CpuMinMin':  1, 'Cost': 1, 'NumberOfNodes': 3},
    ])
    ra.calculate({})
    assert ra.analyze_df.classification.tolist() == ['Overused', 'Normal']
