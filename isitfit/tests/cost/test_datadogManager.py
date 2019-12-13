from ...cost.datadogManager import DatadogManager, DatadogAssistant, DataNotFoundForHostInDdg, HostNotFoundInDdg, DatadogCached

import pytest
@pytest.mark.skip(reason="Can only test this with live credentials ATM. Need to mock")
def test_datadogman_1():
    ddg = DatadogManager()
    host_id='i-0f31feed76f7fb07c'
    df_all = ddg.get_metrics_all(host_id=host_id)
    assert df_all.shape[0] > 0
    #print(df_all.head())


@pytest.fixture
def datadog_assistant(mocker):
    def factory(series=[], host_list=[]):
      mockreturn = lambda *args, **kwargs: {'series': series, 'status': 'ok'}
      mockee = 'datadog.api.Metric.query'
      mocker.patch(mockee, side_effect=mockreturn)

      mockreturn = lambda *args, **kwargs: {'host_list': host_list}
      mockee = 'datadog.api.Hosts.search'
      mocker.patch(mockee, side_effect=mockreturn)

      dda = DatadogAssistant(None, None, host_id='i-123456')
      return dda

    return factory


class TestDatadogAssistant:

  def test_init(self, datadog_assistant):
    dda = datadog_assistant([])
    assert True

  def test_getMetricsCore_noData(self, datadog_assistant):
    dda = datadog_assistant(series=[])
    with pytest.raises(DataNotFoundForHostInDdg):
      df = dda._get_metrics_core(None, 'Average')

  def test_getMetricsCore_ok(self, datadog_assistant):
    dda = datadog_assistant(series=[{'pointlist': [{'ts_int': 1234567, 'Average': 2}]}])
    df = dda._get_metrics_core(None, 'Average')
    assert df.shape[0]==1

  def test_getMeta_noData(self, datadog_assistant):
    dda = datadog_assistant(host_list=[])
    with pytest.raises(HostNotFoundInDdg):
      df = dda._get_meta()

  def test_getMeta_ok(self, datadog_assistant):
    dda = datadog_assistant(host_list=[{'meta': {'gohai': '{"memory": {"total": "10kB"}}', 'cpuCores': 2}}])
    res = dda._get_meta()
    assert res=={'cpuCores': 2, 'memory_total': 10240}

  def test_getMetricsXxxYyy(self, datadog_assistant):
    pointlist = [{'ts_int': 1234567, 'cpu_idle_min': 2.5, 'cpu_idle_avg': 2.5, 'ram_free_min': 10, 'ram_free_avg': 5}]
    dda = datadog_assistant(
      series=[{'pointlist': pointlist}],
      host_list=[{'meta': {'gohai': '{"memory": {"total": "10kB"}}', 'cpuCores': 2}}],
    )

    actual = dda.get_metrics_cpu_max()
    assert actual.shape[0]==1
    assert actual.shape[1]==3 # columns:  cpu_idle_min                   ts_dt  cpu_used_max

    actual = dda.get_metrics_cpu_avg()
    assert actual.shape[0]==1
    assert actual.shape[1]==3

    actual = dda.get_metrics_ram_max()
    assert actual.shape[0]==1
    assert actual.shape[1]==3

    actual = dda.get_metrics_ram_avg()
    assert actual.shape[0]==1
    assert actual.shape[1]==3


@pytest.fixture
def datadog_manager(mocker):
  def factory():
      mockreturn = lambda *args, **kwargs: None
      mockee = 'datadog.initialize'
      mocker.patch(mockee, side_effect=mockreturn)
      ddm = DatadogManager()
      return ddm

  return factory


@pytest.fixture
def ddgenv_set(monkeypatch):
     monkeypatch.setenv('DATADOG_API_KEY', 'abcdef')
     monkeypatch.setenv('DATADOG_APP_KEY', 'abcdef')


@pytest.fixture
def ddgenv_missing(monkeypatch):
     monkeypatch.delenv('DATADOG_API_KEY')
     monkeypatch.delenv('DATADOG_APP_KEY')


class TestDatadogManager:
  def test_init(self, datadog_manager):
      ddm = datadog_manager()
      assert True # no exception

  def test_isConfigured_true(self, datadog_manager, ddgenv_set):
      ddm = datadog_manager()
      assert ddm.is_configured()

  def test_isConfigured_false(self, datadog_manager, ddgenv_missing):
      ddm = datadog_manager()
      assert not ddm.is_configured()

  def test_perEc2_notConf(self, datadog_manager, ddgenv_missing):
      ddm = datadog_manager()
      assert not ddm.is_configured()
      context_ec2 = {}
      context_ec2 = ddm.per_ec2(context_ec2)
      assert context_ec2['ddg_df'] is None


  def test_perEc2_noData(self, datadog_manager, ddgenv_set):
      class MockInst:
        instance_id = 'i-123456'

      ddm = datadog_manager()
      ddm.get_metrics_all = lambda *args, **kwargs: None

      mock_obj = MockInst()
      context_ec2 = {'ec2_obj': mock_obj}
      context_ec2 = ddm.per_ec2(context_ec2)
      assert context_ec2['ddg_df'] is None


  def test_perEc2_yesData(self, datadog_manager, ddgenv_set):
      class MockInst:
        instance_id = 'i-123456'

      import pandas as pd
      import datetime as dt
      ddg_met = pd.DataFrame({'ts_dt': [dt.datetime.now()]})
      ddm = datadog_manager()
      ddm.get_metrics_all = lambda *args, **kwargs: ddg_met

      mock_obj = MockInst()
      ec2_df = pd.DataFrame({'Timestamp': []})
      context_ec2 = {'ec2_obj': mock_obj, 'ec2_df': ec2_df}
      context_ec2 = ddm.per_ec2(context_ec2)
      assert context_ec2['ddg_df'].shape[0]==1
      assert context_ec2['ddg_df'].shape[1]==1


  def test_getMetricsAll(self, datadog_manager, mocker):
      import pandas as pd

      def mymock(mr, me):
        mockreturn = lambda *args, **kwargs: mr
        mockee = 'isitfit.cost.datadogManager.DatadogAssistant.%s'%me
        mocker.patch(mockee, side_effect=mockreturn)

      mockees = [
        ( pd.DataFrame({'ts_int':[1], 'ts_dt':[2], 'cpu_used_max': [3]}),
         'get_metrics_cpu_max'
        ),
        ( pd.DataFrame({'ts_int':[1], 'ts_dt':[2], 'cpu_used_avg': [3]}),
          'get_metrics_cpu_avg'
        ),
        ( pd.DataFrame({'ts_int':[1], 'ts_dt':[2], 'ram_used_max': [3]}),
          'get_metrics_ram_max'
        ),
        ( pd.DataFrame({'ts_int':[1], 'ts_dt':[2], 'ram_used_avg': [3]}),
          'get_metrics_ram_avg'
        ),
      ]
      for mr, me in mockees: mymock(mr, me)

      ddm = datadog_manager()
      actual = ddm.get_metrics_all('i-123456')

      assert actual.shape[0]==1
      assert actual.shape[1]==5 # columns: ts_dt  cpu_used_max  cpu_used_avg  ram_used_max  ram_used_avg


class TestDatadogCachedGetMetricsAll:
  def test_notReady_noData(self, mocker):
    class MockCacheMan:
      def isReady(self): return False

    # mock parent
    import pandas as pd
    mockreturn = lambda *args, **kwargs: pd.DataFrame()
    mockee = 'isitfit.cost.datadogManager.DatadogManager.get_metrics_all'
    mocker.patch(mockee, side_effect=mockreturn)

    cache_man = MockCacheMan()
    ddc = DatadogCached(cache_man)
    actual = ddc.get_metrics_all('i-123456')
    assert actual is None


  def test_notReady_yesData(self, mocker):
    class MockCacheMan:
      def isReady(self): return False

    # mock parent
    import pandas as pd
    mockreturn = lambda *args, **kwargs: pd.DataFrame({'a': [1,2,3]})
    mockee = 'isitfit.cost.datadogManager.DatadogManager.get_metrics_all'
    mocker.patch(mockee, side_effect=mockreturn)

    cache_man = MockCacheMan()
    ddc = DatadogCached(cache_man)
    actual = ddc.get_metrics_all('i-123456')
    assert actual is not None
    assert actual.shape[0]==3


  def test_yesReady_missCache(self, mocker):
    class MockCacheMan:
      def isReady(self): return True
      def get(self, ck): return None
      def set(self, ck, cv): pass

    # mock parent
    import pandas as pd
    mockreturn = lambda *args, **kwargs: pd.DataFrame()
    mockee = 'isitfit.cost.datadogManager.DatadogManager.get_metrics_all'
    mocker.patch(mockee, side_effect=mockreturn)

    cache_man = MockCacheMan()
    ddc = DatadogCached(cache_man)
    actual = ddc.get_metrics_all('i-123456')
    assert actual is None


  def test_yesReady_hitCache(self, mocker):
    import pandas as pd
    class MockCacheMan:
      def isReady(self): return True
      def get(self, ck): return pd.DataFrame()
      def set(self, ck, cv): pass

    cache_man = MockCacheMan()
    ddc = DatadogCached(cache_man)
    actual = ddc.get_metrics_all('i-123456')
    assert actual is None
