from ....cost.redshift.iterator import RedshiftPerformanceIterator

def test_init():
  rpi = RedshiftPerformanceIterator()
  assert True # no exception

# cannot use mock_cloudwatch
# yields error:
# botocore.exceptions.PaginationError: Error during pagination: The same next token was received twice
#from moto import mock_cloudwatch
#@mock_cloudwatch
def test_handleCluster_notFound(mocker):
  mockreturn = lambda *args, **kwargs: []
  mockee = 'isitfit.cost.redshift.iterator.RedshiftPerformanceIterator._metrics_filter'
  mocker.patch(mockee, side_effect=mockreturn)

  rpi = RedshiftPerformanceIterator()
  dummy_id = 'abc'
  m_i = rpi.handle_cluster(dummy_id)
  assert m_i is None


def test_handleCluster_foundCluster(mocker):
  class MockMetricCluster:
    dimensions = [1]

  mockreturn = lambda *args, **kwargs: [MockMetricCluster]
  mockee = 'isitfit.cost.redshift.iterator.RedshiftPerformanceIterator._metrics_filter'
  mocker.patch(mockee, side_effect=mockreturn)

  rpi = RedshiftPerformanceIterator()
  dummy_id = 'abc'
  m_i = rpi.handle_cluster(dummy_id)
  assert m_i is not None


def test_handleCluster_foundMany(mocker):
  class MockMetricCluster:
    dimensions = [1]

  class MockMetricNode:
    dimensions = [1, 2]

  mockreturn = lambda *args, **kwargs: [MockMetricNode, MockMetricCluster]
  mockee = 'isitfit.cost.redshift.iterator.RedshiftPerformanceIterator._metrics_filter'
  mocker.patch(mockee, side_effect=mockreturn)

  rpi = RedshiftPerformanceIterator()
  dummy_id = 'abc'
  m_i = rpi.handle_cluster(dummy_id)
  assert m_i is not None


def test_handleMetric_empty(mocker):
  mockreturn = lambda *args, **kwargs: {'Datapoints': []}
  mockee = 'isitfit.cost.redshift.iterator.RedshiftPerformanceIterator._metric_get_statistics'
  mocker.patch(mockee, side_effect=mockreturn)

  rpi = RedshiftPerformanceIterator()
  df = rpi.handle_metric(None, None, None)
  assert df is None


def test_handleMetric_notEmpty(mocker):
  import datetime as dt
  dt_now = dt.datetime.utcnow()

  ex_dp = [
    {'Timestamp': dt_now - dt.timedelta(seconds=1)},
    {'Timestamp': dt_now - dt.timedelta(seconds=2)},
    {'Timestamp': dt_now - dt.timedelta(seconds=3)}
  ]
  mockreturn = lambda *args, **kwargs: {'Datapoints': ex_dp}
  mockee = 'isitfit.cost.redshift.iterator.RedshiftPerformanceIterator._metric_get_statistics'
  mocker.patch(mockee, side_effect=mockreturn)

  rpi = RedshiftPerformanceIterator()
  df = rpi.handle_metric(None, None, dt_now)
  assert df is not None


from moto import mock_redshift
@mock_redshift
def test_iterateCore_none(mocker):
  # mock the get regions part
  mockreturn = lambda service: ['us-east-1']
  mockee = 'boto3.session.Session.get_available_regions'
  mocker.patch(mockee, side_effect=mockreturn)

  # test
  rpi = RedshiftPerformanceIterator()
  x = list(rpi.iterate_core())
  assert len(x) == 0


@mock_redshift
def test_iterateCore_exists(mocker):
  # mock the get regions part
  mockreturn = lambda service: ['us-east-1']
  mockee = 'boto3.session.Session.get_available_regions'
  mocker.patch(mockee, side_effect=mockreturn)

  # undo some region settings from before
  import boto3
  boto3.setup_default_session(region_name='us-east-1')

  # create mock redshift
  import boto3
  redshift_client = boto3.client('redshift')
  redshift_client.create_cluster(
    ClusterIdentifier='abc',
    NodeType='abc',
    MasterUsername='abc',
    MasterUserPassword='abc'
  )

  # test
  rpi = RedshiftPerformanceIterator()
  rpi.region_include = ['us-east-1']
  x = list(rpi.iterate_core())
  assert len(x) == 1


# cannot name function "test_iterator" because the filename is as such
# pytest .../test_iterator.py -k 'test_iterator' would run all tests, not just this one
def test_iteratorBuiltin(mocker):
  import datetime as dt
  dt_now = dt.datetime.utcnow()

  # patch 1
  ex_iterateCore = [
    {'ClusterIdentifier': 'abc'}, # no creation time
    {'ClusterIdentifier': 'abc', 'ClusterCreateTime': dt_now}, # with creation time
  ]
  mockreturn = lambda *args, **kwargs: ex_iterateCore
  mockee = 'isitfit.cost.redshift.iterator.RedshiftPerformanceIterator.iterate_core'
  mocker.patch(mockee, side_effect=mockreturn)

  # patch 2
  mockreturn = lambda *args, **kwargs: 1
  mockee = 'isitfit.cost.redshift.iterator.RedshiftPerformanceIterator.handle_cluster'
  mocker.patch(mockee, side_effect=mockreturn)

  # patch 3
  import pandas as pd
  mockreturn = lambda *args, **kwargs: 'a dataframe' #pd.DataFrame()
  mockee = 'isitfit.cost.redshift.iterator.RedshiftPerformanceIterator.handle_metric'
  mocker.patch(mockee, side_effect=mockreturn)

  # test
  rpi = RedshiftPerformanceIterator()
  x = list(rpi)
  assert len(x) == 1
  assert x[0][0] == ex_iterateCore[1]
  assert x[0][1] == 'a dataframe'

