

class TestMainManager:

  def test_addListener_failInvalid(self):
    from ...cost.mainManager import MainManager
    mm = MainManager(None)
    import pytest
    from ...utils import IsitfitCliError
    with pytest.raises(IsitfitCliError) as e:
      # raise exception        
      mm.add_listener('foo', lambda x: x)

    # check error message has "please upgrade" if ctx.obj.is_outdated = True
    # TODO


import pytest
@pytest.fixture
def globalTqdm():
    class CtxWrap:
      obj = {'verbose': False, 'debug': False}

    gt = GlobalTqdm(
      CtxWrap(),
      4
    )
    return gt


from isitfit.cost.mainManager import GlobalTqdm
class TestGlobalTqdm:
  
  def test_init(self, globalTqdm):
    assert globalTqdm.t_track==0

  def test_incrStep(self, globalTqdm):
    globalTqdm.incrStep()
    assert globalTqdm.t_track==1

  def test_close(self, globalTqdm):
    globalTqdm.close()
    assert True # no exception
