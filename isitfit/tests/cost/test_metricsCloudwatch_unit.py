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

    df = ca.stats2df(st, iid, dtnow)
    assert df is not None
    assert df.shape[0] > 0
