# Mostly a copy of test_iterator_redshift
# Need to convert the latter to class
# and inherit here to avoid code redundancy


from isitfit.cost.metrics_cloudwatch import CloudwatchEc2, NoCloudwatchException

import pytest

def test_init():
  rpi = CloudwatchEc2()
  assert True # no exception

# cannot use mock_cloudwatch
# yields error:
# botocore.exceptions.PaginationError: Error during pagination: The same next token was received twice
#from moto import mock_cloudwatch
#@mock_cloudwatch
def test_handleCluster_notFound(mocker):
  mockreturn = lambda *args, **kwargs: []
  mockee = 'isitfit.cost.cloudwatchman.CloudwatchEc2._metrics_filter'
  mocker.patch(mockee, side_effect=mockreturn)

  rpi = CloudwatchEc2()
  dummy_id = 'abc'
  with pytest.raises(NoCloudwatchException):
    m_i = rpi.handle_cluster(dummy_id)


def test_handleCluster_foundCluster(mocker):
  class MockMetricCluster:
    dimensions = [1]

  mockreturn = lambda *args, **kwargs: [MockMetricCluster]
  mockee = 'isitfit.cost.cloudwatchman.CloudwatchEc2._metrics_filter'
  mocker.patch(mockee, side_effect=mockreturn)

  rpi = CloudwatchEc2()
  dummy_id = 'abc'
  m_i = rpi.handle_cluster(dummy_id)
  assert m_i is not None


def test_handleCluster_foundMany(mocker):
  class MockMetricCluster:
    dimensions = [1]

  class MockMetricNode:
    dimensions = [1, 2]

  mockreturn = lambda *args, **kwargs: [MockMetricNode, MockMetricCluster]
  mockee = 'isitfit.cost.cloudwatchman.CloudwatchEc2._metrics_filter'
  mocker.patch(mockee, side_effect=mockreturn)

  rpi = CloudwatchEc2()
  dummy_id = 'abc'
  m_i = rpi.handle_cluster(dummy_id)
  assert m_i is not None


def test_handleMetric_empty(mocker):
  mockreturn = lambda *args, **kwargs: {'Datapoints': []}
  mockee = 'isitfit.cost.cloudwatchman.CloudwatchEc2._metric_get_statistics'
  mocker.patch(mockee, side_effect=mockreturn)

  rpi = CloudwatchEc2()
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
  mockee = 'isitfit.cost.cloudwatchman.CloudwatchEc2._metric_get_statistics'
  mocker.patch(mockee, side_effect=mockreturn)

  rpi = CloudwatchEc2()
  df = rpi.handle_metric(None, None, dt_now)
  assert df is not None



import datetime as dt
dt_now_d = dt.datetime.utcnow()


import pytest
@pytest.fixture(scope='function')
def MockCwResource(mocker):
    class MockMetricsObj:
        dimensions = ['one item']
        def get_statistics(self, *args, **kwargs):
            return {'Datapoints': [{'Timestamp':dt.datetime.now(), 'b':2}]}

    class MockMetricsIterator:
        n = 1
        def filter(self, *args, **kwargs):
            # yield 1 object is ok
            # yield >1 objects triggers exception
            for i in range(self.n):
                yield MockMetricsObj()

    class MyCwResource:
      metrics = MockMetricsIterator()

    return MyCwResource


from moto import mock_ec2, mock_cloudwatch # TODO not in moto:, mock_cloudtrail

class TestCloudwatchEc2:
# Edit 2019-11-18
# After starting to use isitfit.cost.cloudwatchman in mainManager,
# the checks for multiple metrics was dropped as it was useless really.
# Now it just returns the first non-empty entry.
#  @mock_ec2
#  @mock_cloudwatch
#  # @mock_cloudtrail
#  def test_perEc2_failMultiple(self, MockCwResource, mocker):
#    from ...cost.mainManager import MainManager
#    mm = MainManager(None, None)
#
#    # mock resource
#    mcw = MockCwResource()
#    mcw.metrics.n = 2 # set to 2 to trigger exception
#    mockreturn = lambda *args, **kwargs: mcw
#    mockee = 'isitfit.cost.cloudwatchman.CloudwatchBase._cloudwatch_metrics_boto3'
#    mocker.patch(mockee, side_effect=mockreturn)
#
#    # class for ec2_obj
#    class MockEc2Obj:
#      region_name = 'us-west-2'
#      instance_id = 'i1'
#      launch_time = dt_now_d
#
#    ec2_obj = MockEc2Obj()
#
#    import pytest
#    from isitfit.cli.click_descendents import IsitfitCliError
#    with pytest.raises(IsitfitCliError) as e:
#      # raise exception
#      mm._cloudwatch_metrics_cached(ec2_obj)



  @mock_ec2
  @mock_cloudwatch
  # @mock_cloudtrail
  def test_perEc2_ok(self, MockCwResource, mocker):
    from isitfit.cost.metrics_cloudwatch import CloudwatchEc2
    cw = CloudwatchEc2(None)

    # mock resource
    mcw = MockCwResource()
    mcw.metrics.n = 1 # set to 1 to NOT trigger exception
    mockreturn = lambda *args, **kwargs: mcw
    mockee = 'isitfit.cost.cloudwatchman.CloudwatchBase._cloudwatch_metrics_boto3'
    mocker.patch(mockee, side_effect=mockreturn)

    # class for ec2_obj
    class MockEc2Obj:
      region_name = 'us-west-2'
      instance_id = 'i1'
      launch_time = dt_now_d

    ec2_obj = MockEc2Obj()

    cw.per_ec2({'ec2_obj': ec2_obj})
    assert True # no exception

