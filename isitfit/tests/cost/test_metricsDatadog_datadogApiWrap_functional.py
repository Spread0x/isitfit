"""
These tests requires firing up a new ec2 instance and installing the datadog agent on it.
Check isitfit/tests/cost/ec2/test_functional.sh for helper commands

Maybe need to use pytest.mark.skip on these tests, or move them to separate folder with some special automatic ec2 instance provisioning
"""

# Update this instance ID when turning on a new instance with a datadog agent running
HOST_ID_VALID = 'i-0a22ca422859d1cd9'

from isitfit.cost.metrics_datadog import DatadogApiWrap, DataQueryError, DataNotFoundForHostInDdg


import pytest

from isitfit.utils import SECONDS_IN_ONE_DAY


@pytest.fixture(scope='session')
def datadog_api():
    import datadog
    datadog.initialize()
    return datadog.api



def get_startEnd():
    # set start/end
    # Update, use time.time() method instead
    #import datetime as dt
    #from datetime import timedelta
    #dt_now = dt.datetime.now()
    #dt_1w  = dt_now - timedelta(days=7)
    #conv2sec = lambda x: time.mktime(x.timetuple())
    #ue_start = conv2sec(start)
    #ue_end   = conv2sec(end)
    import time
    dt_now = int(time.time())
    dt_1w  = dt_now - SECONDS_IN_ONE_DAY*7
    return dt_now, dt_1w


class TestDatadogApiWrapFunctional:
  """
  Tests to help resolve
  https://github.com/autofitcloud/isitfit/issues/10
  """
  def test_hosts_search_ok(self, datadog_api):
    daw = DatadogApiWrap()
    host_id = HOST_ID_VALID
    h_i = daw.hosts_search(host_id)
    #assert h_i['name']==host_id

    # this should match the ec2 type selected when launching this test instance
    assert h_i['cpuCores']==1
    assert int(h_i['memory_total']/1e9)==4


  def test_hosts_search_notFound(self, datadog_api):
    daw = DatadogApiWrap()
    host_id = 'i-1234566'
    from isitfit.utils import HostNotFoundInDdg
    with pytest.raises(HostNotFoundInDdg):
      h_i = daw.hosts_search(host_id)


  def test_metric_query_cpuIdle_ok(self, datadog_api):
    daw = DatadogApiWrap()
    host_id = HOST_ID_VALID

    # set start/end
    dt_now, dt_1w = get_startEnd()

    query = 'system.cpu.idle{host:%s}.rollup(min,%i)'%(host_id, SECONDS_IN_ONE_DAY)
    df = daw.metric_query(host_id, dt_1w, dt_now, query, 'system.cpu.idle', 'some_name')

    assert df.shape[0] > 0
    assert 'some_name' in df.columns


  def test_metric_query_cpuIdle_errQuery(self, datadog_api):
    daw = DatadogApiWrap()
    host_id = HOST_ID_VALID # exists

    # set start/end
    dt_now, dt_1w = get_startEnd()

    query = 'blabla'
    with pytest.raises(DataQueryError):
      df = daw.metric_query(host_id, dt_1w, dt_now, query, 'inexistant', 'somename')



  def test_metric_query_cpuIdle_errNotFound(self, datadog_api):
    daw = DatadogApiWrap()
    host_id = 'i-12345'

    # set start/end
    dt_now, dt_1w = get_startEnd()

    from isitfit.utils import SECONDS_IN_ONE_DAY
    query = 'system.cpu.idle{host:%s}.rollup(min,%i)'%(host_id, SECONDS_IN_ONE_DAY)

    with pytest.raises(DataNotFoundForHostInDdg):
      df = daw.metric_query(host_id, dt_1w, dt_now, query, 'inexistant', 'somename')


