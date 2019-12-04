def mig20191203a():
  """
  As of 0.17, rm ~/.isitfit/iterator_cache-*pkl
  """
  from isitfit.dotMan import DotMan
  import os
  import glob

  # rm ~/.isitfit/iterator_cache-*pkl
  # since that older path is deprecated in favor of /tmp/isitfit/iterator_cache*pkl
  del_p = os.path.join(DotMan().get_dotisitfit(), 'iterator_cache-*.pkl')
  del_p = os.path.expanduser(del_p) # do I need this?
  del_l = glob.glob(del_p)
  for del_i in del_l: os.unlink(del_i)


def mig20191203b():
  """
  As of 0.17, mv /tmp/isitfit*csv /tmp/isitfit/
  """
  from isitfit.dotMan import DotMan
  import tempfile
  import os
  import glob

  # rm /tmp/isitfit*csv
  # since started to use /tmp/isitfit/isitfit*csv
  del_p = os.path.join(tempfile.gettempdir(), 'isitfit*csv')
  new_tmpdir = DotMan().tempdir()
  del_l = glob.glob(del_p)
  for del_i in del_l:
    # os.unlink(del_i)
    new_i = os.path.basename(del_i)
    new_i = os.path.join(new_tmpdir, new_i)
    os.rename(del_i, new_i)


def mig20191203c():
  """
  As of 0.17, rm -rf /tmp/isitfit_ec2info.cache/
  """
  import tempfile
  import os
  import glob

  del_p = os.path.join(tempfile.gettempdir(), 'isitfit_ec2info.cache')
  import shutil
  shutil.rmtree(del_p, ignore_errors=True)
