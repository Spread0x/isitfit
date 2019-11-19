

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



