from isitfit.cost.metrics_automatic import MetricsAuto

class TestMetricsAuto:
  def test_displayStatus(self):
    metrics = MetricsAuto(None, None)
    metrics.status = {
      'i-1': {'ID': 'i-1', 'datadog': 'ok', 'cloudwatch': 'ok'},
      'i-2': {'ID': 'i-2', 'datadog': 'ok', 'cloudwatch': 'ok'},
    }
    metrics.display_status()
