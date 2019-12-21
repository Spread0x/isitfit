from isitfit.cost.metrics_cloudwatch import CloudwatchAssistant

# Using moto yields "Error during pagination: The same next token was received twice"
# so doing the mock myself
# from moto import mock_cloudwatch

import pytest
@pytest.fixture
def mock_cloudwatch(mocker):
  mockee = 'boto3.setup_default_session'
  mocker.patch(mockee, autospec=True)

  def factory(iterator_dims, response):
    class Metric:
      def __init__(self, ndim): self.dimensions = range(ndim)
      def get_statistics(self, *args, **kwargs): return response

    class Iterator:
      def filter(self, *args, **kwargs):
        return [Metric(x) for x in iterator_dims]

    class Resource:
      metrics = Iterator()

    mockreturn = lambda *args, **kwargs: Resource()
    mockee = 'boto3.resource'
    mocker.patch(mockee, side_effect=mockreturn)

  return factory


class TestCwAssUnit:
  # @mock_cloudwatch
  def test_ok(self, mock_cloudwatch):
    import datetime as dt
    dtnow = dt.datetime.now()

    mock_cloudwatch(
      [3, 1],
      { 'Datapoints': [
          {'Timestamp': dtnow, 'SampleCount': 2, 'Maximum': 3, 'Average': 4, 'Minimum': 5}
        ]
      }
    )

    ca = CloudwatchAssistant()
    ca.set_resource("us-west-2")
    assert True # no exception

    iid = 'i-1'
    it = ca.id2iterator(iid, 'AWS/EC2', 'InstanceId')
    assert it is not None

    me = ca.iterator2metric(it, iid)
    assert me is not None

    st = ca.metric2stats(me)
    assert st is not None

    df = ca.stats2df(st, iid, dtnow, 'AWS/EC2')
    assert df is not None
    assert df.shape[0] > 0


from isitfit.cost.metrics_cloudwatch import CloudwatchEc2, CloudwatchRedshift


from isitfit.tests.cost.test_metricsDatadog import cache_man

@pytest.mark.parametrize("AdapterCls", [CloudwatchEc2, CloudwatchRedshift])
class TestCloudwatchEc2GetMetricsDerived:
  def test_yesReady_yesData(self, mocker, cache_man, AdapterCls):
    # mark as ready
    cache_man.ready = True

    # mock parent
    import pandas as pd
    mockreturn = lambda *args, **kwargs: pd.DataFrame({'a': [1,2,3]})
    mockee = 'isitfit.cost.metrics_cloudwatch.CloudwatchBase.handle_main'
    uncached_get = mocker.patch(mockee, side_effect=mockreturn)

    cwc = AdapterCls(cache_man)
    host_id = 'i-123456'

    # after first call
    actual = cwc.get_metrics_derived(None, host_id, None)
    assert actual is not None
    assert actual.shape[0]==3
    assert uncached_get.call_count == 1 # calls upstream
    assert cache_man.get.call_count == 1 # 1st check in cache
    assert cache_man.set.call_count == 1 # 1st set in cache

    # after 2nd call
    actual = cwc.get_metrics_derived(None, host_id, None)
    assert actual is not None
    assert actual.shape[0]==3
    assert uncached_get.call_count == 1 # no increment
    assert cache_man.get.call_count == 2 # 2nd check in cache
    assert cache_man.set.call_count == 1 # no increment
