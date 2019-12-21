from ...cost.metrics_datadog import DatadogManager, DatadogAssistant, DataNotFoundForHostInDdg, HostNotFoundInDdg, DatadogCached
import pandas as pd
import pytest



@pytest.fixture
def datadog_assistant(mocker):
    def factory(series=[], host_list=[]):
      mockreturn = lambda *args, **kwargs: {'series': series, 'status': 'ok'}
      mockee = 'datadog.api.Metric.query'
      mocker.patch(mockee, side_effect=mockreturn)

      mockreturn = lambda *args, **kwargs: {'total_returned': len(host_list), 'host_list': host_list}
      mockee = 'datadog.api.Hosts.search'
      mocker.patch(mockee, side_effect=mockreturn)

      # set start/end
      import datetime as dt
      from datetime import timedelta
      dt_now = dt.datetime.now()
      dt_1w  = dt_now - timedelta(days=7)

      dda = DatadogAssistant(dt_1w, dt_now, host_id='i-123456')
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
    dda = datadog_assistant(host_list=[{'meta': {'gohai': '{"memory": {"total": "10kB"}}', 'cpuCores': 2}, 'name': 'i-123456'}])
    res = dda._get_meta()
    assert res=={'cpuCores': 2, 'memory_total': 10240}

  def test_getMetricsXxxYyy(self, datadog_assistant):
    pointlist = [{'ts_int': 1234567, 'cpu_idle_min': 2.5, 'cpu_idle_avg': 2.5, 'ram_free_min': 10, 'ram_free_avg': 5}]
    dda = datadog_assistant(
      series=[{'pointlist': pointlist}],
      host_list=[{'meta': {'gohai': '{"memory": {"total": "10kB"}}', 'cpuCores': 2}, 'name': 'i-123456'}],
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


  def test_getMetricsAll(self, datadog_manager, mocker):
      def mymock(mr, me):
        mockreturn = lambda *args, **kwargs: mr
        mockee = 'isitfit.cost.metrics_datadog.DatadogAssistant.%s'%me
        mocker.patch(mockee, side_effect=mockreturn)

      import datetime as dt
      dtnow = dt.datetime.now()

      mockees = [
        ( pd.DataFrame({'ts_int':[1], 'ts_dt':[dtnow], 'cpu_used_max': [3]}),
         'get_metrics_cpu_max'
        ),
        ( pd.DataFrame({'ts_int':[1], 'ts_dt':[dtnow], 'cpu_used_avg': [3]}),
          'get_metrics_cpu_avg'
        ),
        ( pd.DataFrame({'ts_int':[1], 'ts_dt':[dtnow], 'cpu_used_min': [3]}),
         'get_metrics_cpu_min'
        ),
        ( pd.DataFrame({'ts_int':[1], 'ts_dt':[dtnow], 'ram_used_max': [3]}),
          'get_metrics_ram_max'
        ),
        ( pd.DataFrame({'ts_int':[1], 'ts_dt':[dtnow], 'ram_used_avg': [3]}),
          'get_metrics_ram_avg'
        ),
        ( pd.DataFrame({'ts_int':[1], 'ts_dt':[dtnow], 'ram_used_min': [3]}),
          'get_metrics_ram_min'
        ),
        ( pd.DataFrame({'ts_int':[1], 'ts_dt':[dtnow], 'nhours': [3]}),
          'get_metrics_count'
        ),
      ]
      for mr, me in mockees: mymock(mr, me)

      ddm = datadog_manager()
      actual = ddm.get_metrics_all('i-123456')

      assert actual.shape[0]==1
      assert actual.shape[1]==8 # columns: ts_dt  cpu_used_max  cpu_used_avg  cpu_used_min  ram_used_max  ram_used_avg  ram_used_min  nhours



@pytest.fixture
def cache_man(mocker):
    """
    Mocked cache manager
    """
    class MockCacheMan:
      def __init__(self):
        self._map = {}
        self.ready = False

      def isReady(self): return self.ready
      def get(self, key): return self._map.get(key)
      def set(self, key, val): self._map[key] = val

    cache_man = MockCacheMan()
    mocker.spy(cache_man, 'get')
    mocker.spy(cache_man, 'set')
    return cache_man


class TestDatadogCachedGetMetricsDerived:
  def test_notReady_noData(self, mocker, cache_man):
    # mock parent
    # mockreturn = lambda *args, **kwargs: pd.DataFrame()
    def mockreturn(*args, **kwargs): raise DataNotFoundForHostInDdg
    mockee = 'isitfit.cost.metrics_datadog.DatadogManager.get_metrics_all'
    mocker.patch(mockee, side_effect=mockreturn)

    ddc = DatadogCached(cache_man)

    # after first call
    with pytest.raises(DataNotFoundForHostInDdg):
      actual = ddc.get_metrics_derived(None, 'i-123456', None)

    assert cache_man.get.call_count == 0
    assert cache_man.set.call_count == 0
    assert cache_man._map == {}

    # after 2nd call
    with pytest.raises(DataNotFoundForHostInDdg):
      actual = ddc.get_metrics_derived(None, 'i-123456', None)

    assert cache_man.get.call_count == 0
    assert cache_man.set.call_count == 0
    assert cache_man._map == {}


  def test_notReady_yesData(self, mocker, cache_man):
    # mock parent
    mockreturn = lambda *args, **kwargs: pd.DataFrame({'a': [1,2,3]})
    mockee = 'isitfit.cost.metrics_datadog.DatadogManager.get_metrics_all'
    mocker.patch(mockee, side_effect=mockreturn)

    ddc = DatadogCached(cache_man)
    actual = ddc.get_metrics_derived(None, 'i-123456', None)
    assert actual is not None
    assert actual.shape[0]==3

    assert cache_man.get.call_count == 0
    assert cache_man.set.call_count == 0
    assert cache_man._map == {}


  def test_yesReady_noData(self, mocker, cache_man):
    # mark as ready
    cache_man.ready = True

    # mock parent
    # mockreturn = lambda *args, **kwargs: pd.DataFrame()
    def mockreturn(*args, **kwargs): raise DataNotFoundForHostInDdg
    mockee = 'isitfit.cost.metrics_datadog.DatadogManager.get_metrics_all'
    mocker.patch(mockee, side_effect=mockreturn)

    ddc = DatadogCached(cache_man)
    host_id = 'i-123456'

    # after first call
    with pytest.raises(DataNotFoundForHostInDdg):
      actual = ddc.get_metrics_derived(None, host_id, None)

    assert cache_man.get.call_count == 1 # checks cache and doesn't find key
    assert cache_man.set.call_count == 1 # first set key
    assert callable(cache_man._map[ddc.get_key(host_id)])

    # after 2nd call
    with pytest.raises(DataNotFoundForHostInDdg):
      actual = ddc.get_metrics_derived(None, host_id, None)

    assert cache_man.get.call_count == 2 # incremented
    assert cache_man.set.call_count == 1 # no increment
    assert callable(cache_man._map[ddc.get_key(host_id)])


  def test_yesReady_invalidCache(self, mocker, cache_man):
    # enable mocked cache
    cache_man.ready = True

    # set key in cache
    host_id = 'i-123456'
    ddc = DatadogCached(cache_man)
    cache_man._map[ddc.get_key(host_id)] = pd.DataFrame()

    # fetch will raise
    with pytest.raises(Exception):
      actual = ddc.get_metrics_derived(None, host_id, None)


  def test_yesReady_yesData(self, mocker, cache_man):
    # mark as ready
    cache_man.ready = True

    # mock parent
    mockreturn = lambda *args, **kwargs: pd.DataFrame({'a': [1,2,3]})
    mockee = 'isitfit.cost.metrics_datadog.DatadogManager.get_metrics_all'
    uncached_get = mocker.patch(mockee, side_effect=mockreturn)

    ddc = DatadogCached(cache_man)
    host_id = 'i-123456'

    # after first call
    actual = ddc.get_metrics_derived(None, host_id, None)
    assert actual is not None
    assert actual.shape[0]==3
    assert uncached_get.call_count == 1 # calls upstream
    assert cache_man.get.call_count == 1 # 1st check in cache
    assert cache_man.set.call_count == 1 # 1st set in cache

    # after 2nd call
    actual = ddc.get_metrics_derived(None, host_id, None)
    assert actual is not None
    assert actual.shape[0]==3
    assert uncached_get.call_count == 1 # no increment
    assert cache_man.get.call_count == 2 # 2nd check in cache
    assert cache_man.set.call_count == 1 # no increment
