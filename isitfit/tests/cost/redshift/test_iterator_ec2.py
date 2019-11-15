# Mostly a copy of test_iterator_redshift
# Need to convert the latter to class
# and inherit here to avoid code redundancy


from ....cost.redshift.iterator import Ec2Iterator

def test_init():
  rpi = Ec2Iterator()
  assert True # no exception

# cannot use mock_cloudwatch
# yields error:
# botocore.exceptions.PaginationError: Error during pagination: The same next token was received twice
#from moto import mock_cloudwatch
#@mock_cloudwatch
def test_handleCluster_notFound(mocker):
  mockreturn = lambda *args, **kwargs: []
  mockee = 'isitfit.cost.redshift.iterator.Ec2Iterator._metrics_filter'
  mocker.patch(mockee, side_effect=mockreturn)

  rpi = Ec2Iterator()
  dummy_id = 'abc'
  m_i = rpi.handle_cluster(dummy_id)
  assert m_i is None


def test_handleCluster_foundCluster(mocker):
  class MockMetricCluster:
    dimensions = [1]

  mockreturn = lambda *args, **kwargs: [MockMetricCluster]
  mockee = 'isitfit.cost.redshift.iterator.Ec2Iterator._metrics_filter'
  mocker.patch(mockee, side_effect=mockreturn)

  rpi = Ec2Iterator()
  dummy_id = 'abc'
  m_i = rpi.handle_cluster(dummy_id)
  assert m_i is not None


def test_handleCluster_foundMany(mocker):
  class MockMetricCluster:
    dimensions = [1]

  class MockMetricNode:
    dimensions = [1, 2]

  mockreturn = lambda *args, **kwargs: [MockMetricNode, MockMetricCluster]
  mockee = 'isitfit.cost.redshift.iterator.Ec2Iterator._metrics_filter'
  mocker.patch(mockee, side_effect=mockreturn)

  rpi = Ec2Iterator()
  dummy_id = 'abc'
  m_i = rpi.handle_cluster(dummy_id)
  assert m_i is not None


def test_handleMetric_empty(mocker):
  mockreturn = lambda *args, **kwargs: {'Datapoints': []}
  mockee = 'isitfit.cost.redshift.iterator.Ec2Iterator._metric_get_statistics'
  mocker.patch(mockee, side_effect=mockreturn)

  rpi = Ec2Iterator()
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
  mockee = 'isitfit.cost.redshift.iterator.Ec2Iterator._metric_get_statistics'
  mocker.patch(mockee, side_effect=mockreturn)

  rpi = Ec2Iterator()
  df = rpi.handle_metric(None, None, dt_now)
  assert df is not None


from moto import mock_ec2
@mock_ec2
def test_iterateCore_none(mocker):
  # mock the get regions part
  mockreturn = lambda service: ['us-east-1']
  mockee = 'boto3.session.Session.get_available_regions'
  mocker.patch(mockee, side_effect=mockreturn)

  # test
  rpi = Ec2Iterator()
  x = list(rpi.iterate_core())
  assert len(x) == 0


@mock_ec2
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
  redshift_client = boto3.resource('ec2')
  redshift_client.create_instances(
    MinCount = 1,
    MaxCount = 1,
    InstanceType='t2.medium'
  )

  # test
  rpi = Ec2Iterator()
  rpi.region_include=['us-east-1']
  x = list(rpi.iterate_core())
  assert len(x) == 1


# cannot name function "test_iterator" because the filename is as such
# pytest .../test_iterator.py -k 'test_iterator' would run all tests, not just this one
def test_iteratorBuiltin(mocker):
  import datetime as dt
  dt_now = dt.datetime.utcnow()

  # patch 1
  ex_iterateCore = [
    {'InstanceId': 'abc'}, # no creation time
    {'InstanceId': 'abc', 'LaunchTime': dt_now}, # with creation time
  ]
  def mockreturn(*args, **kwargs):
    for x in ex_iterateCore:
      yield x

  mockee = 'isitfit.cost.redshift.iterator.BaseIterator.iterate_core'
  mocker.patch(mockee, side_effect=mockreturn)

  # patch 2
  mockreturn = lambda *args, **kwargs: 1
  mockee = 'isitfit.cost.redshift.iterator.BaseIterator.handle_cluster'
  mocker.patch(mockee, side_effect=mockreturn)

  # patch 3
  import pandas as pd
  mockreturn = lambda *args, **kwargs: 'a dataframe' #pd.DataFrame()
  mockee = 'isitfit.cost.redshift.iterator.BaseIterator.handle_metric'
  mocker.patch(mockee, side_effect=mockreturn)

  # test
  rpi = Ec2Iterator()
  x = list(rpi)
  assert len(x) == 1
  assert x[0][0] == ex_iterateCore[1]
  assert x[0][1] == 'a dataframe'



def test_live_iterateCore():
  import os

  # reset all env vars from moto's mocks
  ev_l = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SECURITY_TOKEN', 'AWS_SESSION_TOKEN', 'AWS_DEFAULT_REGION']
  for ev_i in ev_l:
    if ev_i in os.environ.keys():
      del os.environ[ev_i]
 
  # set to profile
  os.environ["AWS_PROFILE"] = "shadi_shadi"

  from isitfit.cost.redshift.iterator import Ec2Iterator
  iterator = Ec2Iterator()
  expect_n = 4 # as of 2019-11-15

  # res = [x1 for x1 in iterator.iterate_core(just_counting=True)]
  res = list(iterator.iterate_core(just_counting=True))
  assert len(res) == expect_n

  # again with full iteration
  res = list(iterator.iterate_core(just_counting=False))
  assert len(res) == expect_n

  # again with instance iterator
  # Note that this returns 3 entries instead of 4
  # because one instance doesn't have data
  res = list(iterator)
  assert len(res) == 3
