import pytest
@pytest.fixture
def tqdml2_obj():
    class CtxWrap:
      obj = {'verbose': False, 'debug': False}

    from isitfit.tqdmman import TqdmL2Account
    gt = TqdmL2Account(
      CtxWrap(),
      4
    )
    return gt


class TestTqdmL2Account:
  
  def test_init(self, tqdml2_obj):
    assert tqdml2_obj.t_track==0

  def test_incrStep(self, tqdml2_obj):
    tqdml2_obj.incrStep()
    assert tqdml2_obj.t_track==1

  def test_close(self, tqdml2_obj):
    tqdml2_obj.close()
    assert True # no exception
