from ...tags.tagsPush import TagsPush
import pytest
from isitfit.cli.click_descendents import IsitfitCliError


def getTempFile():
  import tempfile
  from isitfit.dotMan import DotMan
  fh = tempfile.NamedTemporaryFile(suffix='.csv', prefix='isitfit-testTagsPush-', delete=True, dir=DotMan().tempdir())
  return fh


def test_validateTagsFile_fail_empty():
  with getTempFile() as fh:
    tp = TagsPush(fh.name, None)
    with pytest.raises(IsitfitCliError) as e_info:
      tp.read_csv()
      # tp.validateTagsFile()


def test_validateTagsFile_fail_format_1():
  import pandas as pd
  df = pd.DataFrame([
    {'A': 'abc', 'B': 'some instance'},
    {'A': 'def', 'B': 'some instance'},
  ])
  with getTempFile() as fh:
    df.to_csv(fh.name, index=False)
    tp = TagsPush(fh.name, None)
    with pytest.raises(IsitfitCliError) as e_info:
      tp.read_csv()


def test_validateTagsFile_fail_format_2():
  import pandas as pd
  df = pd.DataFrame([
    {'instance_id': 'i-1', 'A': 'abc', 'B': 'some instance'},
    {'instance_id': 'i-2', 'A': 'def', 'B': 'some instance'},
  ])
  with getTempFile() as fh:
    df.to_csv(fh.name, index=False)
    tp = TagsPush(fh.name, None)
    tp.read_csv()
    with pytest.raises(IsitfitCliError) as e_info:
      tp.validateTagsFile()


def test_validateTagsFile_ok():
  import pandas as pd
  df = pd.DataFrame([
    {'instance_id': 'i-1', 'Name': 'some instance', 'Environment': 'Dev'},
    {'instance_id': 'i-2', 'Name': 'another instance', 'Environment': 'Dev'},
    {'instance_id': 'i-2', 'Name': 'another instance', 'Environment': 'Dev'},
  ])
  with getTempFile() as fh:
    df.to_csv(fh.name, index=False)
    tp = TagsPush(fh.name, None)
    tp.read_csv()
    tp.validateTagsFile()

#-----------------------

def test_diffLatest_fail_noChanges(monkeypatch):
  """
  No changes detected
  """
  import pandas as pd
  tags_old = pd.DataFrame([
    {'instance_id': 'i-1', 'Name': 'some instance', 'Environment': 'Dev'},
    {'instance_id': 'i-2', 'Name': 'another instance', 'Environment': 'Dev'},
  ])
  tags_new = tags_old.copy()

  # perform diff
  tp = TagsPush(None, None)
  tp.csv_df = tags_new
  tp.latest_df = tags_old
  with pytest.raises(IsitfitCliError) as e_info:
    tp.diffLatest()



def test_diffLatest_fail_newInstances(monkeypatch):
  """
  Some instance IDs in new but not in old
  """
  import pandas as pd
  tags_old = pd.DataFrame([
    {'instance_id': 'i-1'},
    {'instance_id': 'i-2'},
  ])
  tags_new = pd.DataFrame([
    {'instance_id': 'i-1'},
    {'instance_id': 'i-3'},
  ])

  # perform diff
  tp = TagsPush(None, None)
  tp.csv_df = tags_new
  tp.latest_df = tags_old
  with pytest.raises(IsitfitCliError) as e_info:
    tp.diffLatest()


def test_diffLatest_fail_dropIsWrong(monkeypatch):
  """
  Environment tag is dropped but user disagrees
  """
  import pandas as pd
  tags_old = pd.DataFrame([
    {'instance_id': 'i-1', 'Name': 'some instance', 'Environment': 'Dev'},
    {'instance_id': 'i-2', 'Name': 'another instance', 'Environment': 'Dev'},
  ])
  tags_new = pd.DataFrame([
    {'instance_id': 'i-1', 'Name': 'some instance'},
    {'instance_id': 'i-2', 'Name': 'another instance'},
  ])

  # How to test a function with input call?
  # https://stackoverflow.com/a/36377194/4126114
  # monkeypatch the "input" function, so that it returns "Mark".
  # This simulates the user entering "Mark" in the terminal:
  monkeypatch.setattr('builtins.input', lambda x: "no")

  # perform diff
  tp = TagsPush(None, None)
  tp.csv_df = tags_new
  tp.latest_df = tags_old
  with pytest.raises(IsitfitCliError) as e_info:
    tp.diffLatest()



def test_diffLatest_ok(monkeypatch):
  """
  Environment tag is dropped but user disagrees
  """
  import pandas as pd
  tags_old = pd.DataFrame([
    {'instance_id': 'i-1', 'Name': 'some instance', 'Environment': 'Dev', 'App': 'db'},
    {'instance_id': 'i-2', 'Name': 'another instance', 'Environment': 'Dev', 'App': 'db'},
  ])
  tags_new = pd.DataFrame([
    {'instance_id': 'i-1', 'Name': 'some instance', 'Owner': 'shadi', 'Application': 'db'},
    {'instance_id': 'i-2', 'Name': 'another instance', 'Owner': 'tarzan', 'Application': 'db'},
  ])

  # How to test a function with input call?
  # https://stackoverflow.com/a/36377194/4126114
  # monkeypatch the "input" function, so that it returns "Mark".
  # This simulates the user entering "Mark" in the terminal:
  monkeypatch.setattr('builtins.input', lambda x: "yes")

  # perform diff
  tp = TagsPush(None, None)
  tp.csv_df = tags_new
  tp.latest_df = tags_old
  tp.diffLatest()
  actual_mig = tp.mig_df

  expected_mig = pd.DataFrame([
    {'action': 'mv',    'old': 'App',         'new': 'Application'},
    {'action': 'touch', 'old': None,          'new': 'Owner'},
    {'action': 'rm',    'old': 'Environment', 'new': None},
  ])
  pd.testing.assert_frame_equal(actual_mig, expected_mig)
