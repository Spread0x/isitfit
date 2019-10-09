def test_get_myuid():
  from .utils import get_myuid
  uuid_val = get_myuid()
  assert True

def test_ping_matomo():
  from .utils import ping_matomo
  ping_matomo("/test")
  assert True
