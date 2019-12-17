from isitfit.cost.metrics_cloudwatch import CloudwatchRedshift
import pytest
from isitfit.cost.metrics_cloudwatch import NoCloudwatchException


def test_init():
  rpi = CloudwatchRedshift()
  assert True # no exception

# cannot use mock_cloudwatch
# yields error:
# botocore.exceptions.PaginationError: Error during pagination: The same next token was received twice
#from moto import mock_cloudwatch
#@mock_cloudwatch
def test_handleCluster_notFound(mocker):
  mockreturn = lambda *args, **kwargs: []
  mockee = 'isitfit.cost.cloudwatchman.CloudwatchRedshift._metrics_filter'
  mocker.patch(mockee, side_effect=mockreturn)

  rpi = CloudwatchRedshift()
  dummy_id = 'abc'

  with pytest.raises(NoCloudwatchException):
    m_i = rpi.handle_cluster(dummy_id)


def test_handleCluster_foundCluster(mocker):
  class MockMetricCluster:
    dimensions = [1]

  mockreturn = lambda *args, **kwargs: [MockMetricCluster]
  mockee = 'isitfit.cost.cloudwatchman.CloudwatchRedshift._metrics_filter'
  mocker.patch(mockee, side_effect=mockreturn)

  rpi = CloudwatchRedshift()
  dummy_id = 'abc'
  m_i = rpi.handle_cluster(dummy_id)
  assert m_i is not None


def test_handleCluster_foundMany(mocker):
  class MockMetricCluster:
    dimensions = [1]

  class MockMetricNode:
    dimensions = [1, 2]

  mockreturn = lambda *args, **kwargs: [MockMetricNode, MockMetricCluster]
  mockee = 'isitfit.cost.cloudwatchman.CloudwatchRedshift._metrics_filter'
  mocker.patch(mockee, side_effect=mockreturn)

  rpi = CloudwatchRedshift()
  dummy_id = 'abc'
  m_i = rpi.handle_cluster(dummy_id)
  assert m_i is not None


def test_handleMetric_empty(mocker):
  mockreturn = lambda *args, **kwargs: {'Datapoints': []}
  mockee = 'isitfit.cost.cloudwatchman.CloudwatchRedshift._metric_get_statistics'
  mocker.patch(mockee, side_effect=mockreturn)

  rpi = CloudwatchRedshift()
  with pytest.raises(NoCloudwatchException):
    df = rpi.handle_metric(None, None, None)



def test_handleMetric_notEmpty(mocker):
  import datetime as dt
  dt_now = dt.datetime.utcnow()

  ex_dp = [
    {'Timestamp': dt_now - dt.timedelta(seconds=1)},
    {'Timestamp': dt_now - dt.timedelta(seconds=2)},
    {'Timestamp': dt_now - dt.timedelta(seconds=3)}
  ]
  mockreturn = lambda *args, **kwargs: {'Datapoints': ex_dp}
  mockee = 'isitfit.cost.cloudwatchman.CloudwatchRedshift._metric_get_statistics'
  mocker.patch(mockee, side_effect=mockreturn)

  rpi = CloudwatchRedshift()
  df = rpi.handle_metric(None, None, dt_now)
  assert df is not None


