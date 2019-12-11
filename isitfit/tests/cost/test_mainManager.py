

class TestMainManager:

  def test_addListener_failInvalid(self):
    from ...cost.mainManager import MainManager
    mm = MainManager(None, None)
    import pytest
    from isitfit.cli.click_descendents import IsitfitCliError
    with pytest.raises(IsitfitCliError) as e:
      # raise exception        
      mm.add_listener('foo', lambda x: x)

    # check error message has "please upgrade" if ctx.obj.is_outdated = True
    # TODO



