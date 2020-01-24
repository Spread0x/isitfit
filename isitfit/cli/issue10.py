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
  datadog_hostname = None

  def test_hosts(self, datadog_api):
    # check total numbers and display message in case of failure later
    h_all = datadog_api.Hosts.totals()
    print("Found {total_up} ec2 hosts that are UP, and {total_active} that are active".format(**h_all))
    assert h_all['total_up'] > 0
    assert h_all['total_active'] > 0

    # search without filter
    # print a list of 5 ec2 IDs in case of error when searching for specific ID below
    MAX_HOSTS = 5 # limit just in case
    h_search_count = datadog_api.Hosts.search(count=MAX_HOSTS)
    import pdb
    pdb.set_trace()
    print("first %i IDs found (aws_id, name, host_name): "%MAX_HOSTS, [tuple(hi.get(k) for k in ['aws_id', 'name', 'host_name']) for hi in h_search_count['host_list']])
    print("datadog_api.Hosts.search(count=%i) full output:"%MAX_HOSTS)
    for i, hi in enumerate(h_search_count['host_list']): print("%i: "%i, hi)
    assert len(h_search_count['host_list']) > 0
    assert h_search_count['total_returned'] > 0

    # now search for provided ID
    h_all = datadog_api.Hosts.search(filter='host:%s'%self.datadog_hostname)
    assert len(h_all['host_list']) > 0
    assert h_all['total_returned'] == 1
    # alternatively can check host_name
    assert h_all['host_list'][0]['name']==self.datadog_hostname


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
    query = 'system.cpu.idle{host:%s}.rollup(min,%i)'%(self.datadog_hostname, SECONDS_IN_ONE_DAY)

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
@click.argument('datadog_hostname') #, help='Instance ID on which to run this test')
def issue10(datadog_hostname):
  """
  Click command that runs test through pytest
  """
  TestIssue10.datadog_hostname = datadog_hostname

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
