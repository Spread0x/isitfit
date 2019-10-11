def test_ping_matomo():
  from ..utils import ping_matomo
  ping_matomo("/test")
  assert True
