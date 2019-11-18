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

class TestMainManager:

  def test_addListener_failInvalid(self):
    from ...cost.mainManager import MainManager
    mm = MainManager(None, None, None)
    import pytest
    from ...utils import IsitfitCliError
    with pytest.raises(IsitfitCliError) as e:
      # raise exception        
      mm.add_listener('foo', lambda x: x)

    # check error message has "please upgrade" if ctx.obj.is_outdated = True
    # TODO


# Edit 2019-11-18
# After starting to use isitfit.cost.redshift.cloudwatchman in mainManager,
# the checks for multiple metrics was dropped as it was useless really.
# Now it just returns the first non-empty entry.
#  @mock_ec2
#  @mock_cloudwatch
#  # @mock_cloudtrail
#  def test_CwMetricsCore_failMultiple(self, MockCwResource, mocker):
#    from ...cost.mainManager import MainManager
#    mm = MainManager(None, None, None)
#
#    # mock resource
#    mcw = MockCwResource()
#    mcw.metrics.n = 2 # set to 2 to trigger exception
#    mockreturn = lambda *args, **kwargs: mcw
#    mockee = 'isitfit.cost.redshift.cloudwatchman.CloudwatchBase._cloudwatch_metrics_boto3'
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
#    from ...utils import IsitfitCliError
#    with pytest.raises(IsitfitCliError) as e:
#      # raise exception
#      mm._cloudwatch_metrics_cached(ec2_obj)



  @mock_ec2
  @mock_cloudwatch
  # @mock_cloudtrail
  def test_CwMetricsCore_ok(self, MockCwResource, mocker):
    from ...cost.mainManager import MainManager
    mm = MainManager(None, None, None)

    # mock resource
    mcw = MockCwResource()
    mcw.metrics.n = 1 # set to 1 to NOT trigger exception
    mockreturn = lambda *args, **kwargs: mcw
    mockee = 'isitfit.cost.redshift.cloudwatchman.CloudwatchBase._cloudwatch_metrics_boto3'
    mocker.patch(mockee, side_effect=mockreturn)

    # class for ec2_obj
    class MockEc2Obj:
      region_name = 'us-west-2'
      instance_id = 'i1'
      launch_time = dt_now_d

    ec2_obj = MockEc2Obj()

    import pytest
    from ...utils import IsitfitCliError
    mm._cloudwatch_metrics_cached(ec2_obj)
    assert True # no exception

