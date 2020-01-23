"""
pytest tests to figure out a solution for https://github.com/autofitcloud/isitfit/issues/10
"Missing memory data"
isitfit unable to pick up data from datadog for a particular instance, despite the data's availability
"""

import pytest

@pytest.fixture(scope='session')
def datadog_api():
    import datadog
    datadog.initialize()
    return datadog.api


class TestIssue10:
  """
  Tests to help resolve
  https://github.com/autofitcloud/isitfit/issues/10
  """
  host_id = None

  def test_hosts_search(self, datadog_api):
    h_all = datadog_api.Hosts.search(filter='host:%s'%self.host_id)
    assert len(h_all['host_list']) > 0
    assert h_all['total_returned'] == 1
    assert h_all['host_list'][0]['name']==self.host_id


  def test_metric_query_cpuIdle(self, datadog_api):
    # set start/end
    import datetime as dt
    from datetime import timedelta
    dt_now = dt.datetime.now()
    dt_1w  = dt_now - timedelta(days=7)

    # convert to seconds since unix epoch
    # https://stackoverflow.com/a/6999787/4126114
    import time
    conv2sec = lambda x: time.mktime(x.timetuple())
    ue_now = conv2sec(dt_now)
    ue_1w  = conv2sec(dt_1w)

    # build query
    from isitfit.utils import SECONDS_IN_ONE_DAY
    query = 'system.cpu.idle{host:%s}.rollup(min,%i)'%(self.host_id, SECONDS_IN_ONE_DAY)

    # query datadog
    # https://docs.datadoghq.com/api/?lang=python#query-timeseries-points
    m = datadog_api.Metric.query(start=ue_1w, end=ue_now, query=query)

    if 'errors' in m:
      print(m)
      raise Exception(m['errors'])

    if m['status'] != 'ok':
      raise Exception(m['status'])

    assert len(m['series'])>0


import click
from isitfit.cli.click_descendents import IsitfitCommand
@click.command(help='Tests to debug github issue #10', cls=IsitfitCommand, hidden=True)
@click.argument('host_id') #, help='Instance ID on which to run this test')
def issue10(host_id):
  """
  Click command that runs test through pytest
  """
  TestIssue10.host_id = host_id

  # https://docs.pytest.org/en/latest/usage.html#calling-pytest-from-python-code
  exit_code = pytest.main([__file__, '--verbose'])
  conclude_msg = ""
  conclude_color = ""
  if exit_code != 0:
    conclude_msg = "isitfit: Tests for issue #10 failed"
    conclude_color = "red"
  else:
    conclude_msg = "isitfit: Tests for issue #10 passed"
    conclude_color = "green"

  import click
  click.secho(conclude_msg, fg=conclude_color)
  click.secho("More details at https://github.com/autofitcloud/isitfit/issues/10")
