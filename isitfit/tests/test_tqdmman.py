import pytest
@pytest.fixture
def tqdml2_obj():
    class CtxWrap:
      obj = {'verbose': False, 'debug': False}

    from isitfit.tqdmman import TqdmL2Quiet
    gt = TqdmL2Quiet(
      CtxWrap()
    )
    return gt


class TestTqdmL2Quiet:
  
  def test_init(self, tqdml2_obj):
    x_iterator = tqdml2_obj([])
    x_list = list(x_iterator)
    assert True # no exception
    assert len(x_list)==0
