"""
Unit tests for python exception handling.
Purpose is to understand how this works exactly
"""


import pytest


def test_finally():
  class DoIt:
    x=1
    def doit(self):
      try:
        raise Exception
      except ValueError:
        self.x=2
      finally:
        self.x=3

  y=DoIt()
  with pytest.raises(Exception):
    y.doit()
    assert False # should not be reached

  # after exception
  assert y.x==3


def test_multiExcept():
  class E1(ValueError): pass
  class E2(ValueError): pass

  def doit(et):
    x=1
    try:
      raise et
    except E1:
      x=2
    except E2:
      x=3
    except:
      raise

    return x

  assert doit(E1())==2
  assert doit(E2())==3

  with pytest.raises(Exception):
    doit(Exception())
