class TestDotMan:

  def test_get_myuid_simple(self):
    from ..dotMan import DotMan
    uuid_val = DotMan().get_myuid()
    assert True

  # functional test
  def test_get_myuid_unavailable(self, monkeypatch):
    import tempfile
    from ..dotMan import DotMan
    dm = DotMan()
    with tempfile.TemporaryDirectory(prefix="isitfit-test-") as td:
      def mockreturn(): return td
      monkeypatch.setattr(dm, "get_dotisitfit", mockreturn)

      import os
      assert not os.path.isfile(os.path.join(td, "uid.txt"))
      uuid_val = dm.get_myuid()
      assert True

  # functional test
  def test_get_myuid_overwritten(self, monkeypatch):
    import tempfile
    from ..dotMan import DotMan
    dm = DotMan()
    with tempfile.TemporaryDirectory(prefix="isitfit-test-") as td:
      def mockreturn(): return td
      monkeypatch.setattr(dm, "get_dotisitfit", mockreturn)

      import os
      p3_uidtxt = os.path.join(td, "uid.txt")
      # overwrite
      with open(p3_uidtxt, 'w') as fh:
        fh.write("bla")

      # test core
      uuid_val = dm.get_myuid()
      assert uuid_val != "bla"
      assert len(uuid_val)==32



