import datetime as dt

import pytest
@pytest.fixture(scope='function')
def MockCwResource(mocker):
    class MockMetricsObj:
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


  @mock_ec2
  @mock_cloudwatch
  # @mock_cloudtrail
  def test_CwMetricsCore_failMultiple(self, MockCwResource):
    from ...cost.mainManager import MainManager
    mm = MainManager(None, None, None)

    # mock resource
    mm.cloudwatch_resource = MockCwResource()
    mm.cloudwatch_resource.metrics.n = 2 # set to 2 to trigger exception

    # class for ec2_obj
    class MockEc2Obj:
      instance_id = 1

    ec2_obj = MockEc2Obj()

    import pytest
    from ...utils import IsitfitCliError
    with pytest.raises(IsitfitCliError) as e:
      # raise exception
      mm._cloudwatch_metrics_core(ec2_obj)



  @mock_ec2
  @mock_cloudwatch
  # @mock_cloudtrail
  def test_CwMetricsCore_ok(self, MockCwResource):
    from ...cost.mainManager import MainManager
    mm = MainManager(None, None, None)

    # mock resource
    mm.cloudwatch_resource = MockCwResource()
    mm.cloudwatch_resource.metrics.n = 1 # set to 1 to NOT trigger exception

    # class for ec2_obj
    class MockEc2Obj:
      instance_id = 1

    ec2_obj = MockEc2Obj()

    import pytest
    from ...utils import IsitfitCliError
    mm._cloudwatch_metrics_core(ec2_obj)
    assert True # no exception

