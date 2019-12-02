# Mostly a copy of test_iterator_redshift
# Need to convert the latter to class
# and inherit here to avoid code redundancy


from ....cost.ec2_analyze import Ec2Iterator

def test_init():
  rpi = Ec2Iterator()
  assert True # no exception


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
  ec2_client = boto3.resource('ec2')
  ec2_client.create_instances(
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
@mock_ec2
def test_iteratorBuiltin(mocker):
  # create an instance
  import boto3
  ec2_client = boto3.resource('ec2')
  response_created = ec2_client.create_instances(
    MinCount = 1,
    MaxCount = 1,
    InstanceType='t2.medium'
  )
  response_created = response_created[0]

  # proceed
  import datetime as dt
  dt_now = dt.datetime.utcnow()

  # patch 1
  ex_iterateCore = [
    {'Region': 'us-east-1', 'InstanceId': response_created.instance_id}, # no creation time
    {'Region': 'us-east-1', 'InstanceId': response_created.instance_id, 'LaunchTime': dt_now}, # with creation time
  ]
  def mockreturn(*args, **kwargs):
    for x in ex_iterateCore:
      yield x

  mockee = 'isitfit.cost.base_iterator.BaseIterator.iterate_core'
  mocker.patch(mockee, side_effect=mockreturn)

  # patch 2
  #mockreturn = lambda *args, **kwargs: 1
  #mockee = 'isitfit.cost.base_iterator.BaseIterator.handle_cluster'
  #mocker.patch(mockee, side_effect=mockreturn)

  # patch 3
  ## import pandas as pd
  #mockreturn = lambda *args, **kwargs: 'a dataframe' #pd.DataFrame()
  #mockee = 'isitfit.cost.base_iterator.BaseIterator.handle_metric'
  #mocker.patch(mockee, side_effect=mockreturn)

  # test
  rpi = Ec2Iterator()
  x = list(rpi)
  assert len(x) == 1
  assert x[0][3] == response_created



def test_live_iterateCore():
  import os

  # reset all env vars from moto's mocks
  ev_l = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SECURITY_TOKEN', 'AWS_SESSION_TOKEN', 'AWS_DEFAULT_REGION']
  for ev_i in ev_l:
    if ev_i in os.environ.keys():
      del os.environ[ev_i]
 
  # set to profile
  os.environ["AWS_PROFILE"] = "shadi_shadi"

  iterator = Ec2Iterator()
  expect_n = 4 # as of 2019-11-15

  # res = [x1 for x1 in iterator.iterate_core()]
  res = list(iterator.iterate_core())
  assert len(res) == expect_n

  # again with full iteration
  res = list(iterator)
  assert len(res) == expect_n

  # again with instance iterator
  # Note that this returns 3 entries instead of 4
  # because one instance doesn't have data
  # Edit 2019-11-18: moved cloudwatch part out of iterator,
  # and hence this returns 4 again
  res = list(iterator)
  assert len(res) == expect_n
