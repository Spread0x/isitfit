import os

class DotMan:
  def get_dotisitfit(self):
    # get home
    import pathlib
    p1_home = str(pathlib.Path.home())

    # check dot folder
    p2_dot = os.path.join(p1_home, ".isitfit")
    if not os.path.exists(p2_dot):
      pathlib.Path(p2_dot).mkdir(exist_ok=True)

    return p2_dot


  def get_myuid(self, is_reentry=False):
    """
    Create a UUID for each installation of isitfit
    This also creates a .isitfit folder in the user's home directory
    and caches the generated UUID in a txt file for re-use

    is_reentry - internally used flag to identify that this is a case when
                 UUID is identified as invalid and needs to be set again
    """
    p2_dot = self.get_dotisitfit()

    # check uid file within dot folder
    p3_uidtxt = os.path.join(p2_dot, "uid.txt")
    uuid_val = None
    if not os.path.exists(p3_uidtxt):
      import uuid
      uuid_val = uuid.uuid4().hex
      with open(p3_uidtxt, 'w') as fh:
        fh.write(uuid_val)

    # if not created above, read from file
    if uuid_val is None:
      with open(p3_uidtxt, 'r') as fh:
        uuid_val = fh.read()
        uuid_val = uuid_val.strip() # strip the new-line or spaces if any

    # if re-entry due to invalid ID or not
    if is_reentry:
      # any further processing of this would be an overkill
      pass
    else:
      # verify that the UUID is valid (in case of accidental overwrite)
      if len(uuid_val)!=32:
        # drop the uid.txt file and overwrite it
        os.remove(p3_uidtxt)
        uuid_val = self.get_myuid(True)

    # return
    return uuid_val


  def tempdir(self):
    import os
    import tempfile
    isitfit_tmpdir = os.path.join(tempfile.gettempdir(), 'isitfit')
    os.makedirs(isitfit_tmpdir, exist_ok=True)
    return isitfit_tmpdir


import os
class DotFile:
  """
  Base class to set/get files in ~/.isitfit like ~/.isitfit/last_email.txt
  """
  filename = None
  def __init__(self):
    self._init_fn()

  def _init_fn(self):
    if self.filename is None:
      raise Exception("Derived classes should set filename member")

    from isitfit.dotMan import DotMan
    dm = DotMan()
    fold = dm.get_dotisitfit()
    self.fn = os.path.join(fold, self.filename)

  def get(self):
    if not os.path.exists(self.fn):
      return None

    with open(self.fn, 'r') as fh:
      val = fh.read()
      val = val.strip()

      if val=='':
        return None

      return val

  def set(self, val):
    with open(self.fn, 'w') as fh:
      fh.write(val)


class DotLastEmail(DotFile):
  filename = "last_email.txt"


class DotLastProfile(DotFile):
  filename = "last_profile.txt"
