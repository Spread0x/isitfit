from isitfit.cost.metrics_automatic import MetricsAuto

class TestMetricsAuto:
  def test_displayStatus(self):
    metrics = MetricsAuto(None, None)
    metrics.status = {
      'i-1': {'ID': 'i-1', 'datadog': 'ok', 'cloudwatch': 'ok'},
      'i-2': {'ID': 'i-2', 'datadog': 'ok', 'cloudwatch': 'ok'},
    }
    metrics.display_status()


"""
  # Tests moved from test_metricsDatadog after its per_ec2 (listener class) was deprecated in favor of the metrics_automatic listener
  # Need to uncomment these tests some day and fix them for running on the metrics_automatic listener

  def test_perEc2_notConf(self, datadog_manager, ddgenv_missing):
      ddm = datadog_manager()
      assert not ddm.is_configured()
      context_ec2 = {}
      context_ec2 = ddm.per_ec2(context_ec2)
      assert context_ec2['ddg_df'] is None


  def test_perEc2_noData(self, datadog_manager, ddgenv_set):
      class MockInst:
        instance_id = 'i-123456'

      ddm = datadog_manager()
      ddm.get_metrics_all = lambda *args, **kwargs: None

      mock_obj = MockInst()
      context_ec2 = {'ec2_obj': mock_obj}
      context_ec2 = ddm.per_ec2(context_ec2)
      assert context_ec2['ddg_df'] is None


  def test_perEc2_yesData(self, datadog_manager, ddgenv_set):
      class MockInst:
        instance_id = 'i-123456'

      import datetime as dt
      ddg_met = pd.DataFrame({'ts_dt': [dt.datetime.now()]})
      ddm = datadog_manager()
      ddm.get_metrics_all = lambda *args, **kwargs: ddg_met

      mock_obj = MockInst()
      ec2_df = pd.DataFrame({'Timestamp': []})
      context_ec2 = {'ec2_obj': mock_obj, 'ec2_df': ec2_df}
      context_ec2 = ddm.per_ec2(context_ec2)
      assert context_ec2['ddg_df'].shape[0]==1
      assert context_ec2['ddg_df'].shape[1]==1
"""
