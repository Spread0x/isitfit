# mocker fixture becomes available after installing pytest-mock
# https://github.com/pytest-dev/pytest-mock
def test_ping_matomo(mocker):
  from ..utils import ping_matomo
  def mockreturn(url, json, timeout): return "foo"
  mocked_post = mocker.patch('isitfit.utils.requests.post', side_effect=mockreturn)
  ping_matomo("/test")

  # check that mocked object is called
  # https://github.com/pytest-dev/pytest-mock/commit/68868872195135bdb90d45a5cb0d609400943eae
  mocked_post.assert_called()



def test_isitfitCliError():
    import pytest
    from ..utils import IsitfitCliError

    class MockContext:
        obj = {'bar': 1}
        command = None

    ctx = MockContext()
    with pytest.raises(IsitfitCliError) as e:
        raise IsitfitCliError("foo", ctx)
