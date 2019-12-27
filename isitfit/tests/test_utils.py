import pytest


# mocker fixture becomes available after installing pytest-mock
# https://github.com/pytest-dev/pytest-mock
def test_pingMatomo_unit(mocker):
  from ..utils import ping_matomo
  def mockreturn(url, json, timeout): return "foo"
  mocked_post = mocker.patch('isitfit.utils.requests.post', side_effect=mockreturn)
  ping_matomo("/test")

  # check that mocked object is called
  # https://github.com/pytest-dev/pytest-mock/commit/68868872195135bdb90d45a5cb0d609400943eae
  mocked_post.assert_called()



def test_pingMatomo_functional(mocker):
  from ..utils import ping_matomo
  ping_matomo("/test")





def test_isitfitCliError():
    from isitfit.cli.click_descendents import IsitfitCliError

    class MockContext:
        obj = {'bar': 1}
        command = None

    ctx = MockContext()
    with pytest.raises(IsitfitCliError) as e:
        raise IsitfitCliError("foo", ctx)



def test_mergeSeriesOnTimestampRange():
  import pandas as pd
  df_cpu = pd.DataFrame({'Timestamp': [1,2,3,4], 'field_1': [5,6,7,8]})
  df_type = pd.DataFrame({'Timestamp': [1,3], 'field_2': ['a','b']})

  # update 2019-11-20 had initially written example as field_2: a, a, b, b
  # but maybe that was an outdated example
  expected = pd.DataFrame({'Timestamp': [1,2,3,4], 'field_1': [5,6,7,8], 'field_2': ['a','b','b','b']})

  # reverse sort
  df_cpu  = df_cpu.sort_values(['Timestamp'], ascending=False)
  df_type = df_type.sort_values(['Timestamp'], ascending=False)

  # set index
  df_type = df_type.set_index('Timestamp')

  # test
  from ..utils import mergeSeriesOnTimestampRange
  actual = mergeSeriesOnTimestampRange(df_cpu, df_type, ['field_2'])

  # straight sort
  actual = actual.sort_values(['Timestamp'], ascending=True)

  #print(expected)
  #print(actual)
  pd.testing.assert_frame_equal(expected, actual)


def test_b2l():
  from isitfit.utils import b2l
  a = b2l(True)
  assert a=='T'
  a = b2l(False)
  assert a=='F'



def test_l2s():
  from isitfit.utils import l2s
  a = l2s(list(range(10)))
  assert a=='0,1,...,8,9'


# https://stackoverflow.com/a/40884671/4126114
@pytest.mark.parametrize("filter_val,expect_out", [(None, 'app = isitfit\napp = another'), ('is', 'app = isitfit'), ('foo', '')])
def test_taglist2str(filter_val, expect_out):
  from isitfit.utils import taglist2str

  a = taglist2str([{'Key':'app', 'Value':'isitfit'}, {'Key':'app', 'Value':'another'}], filter_val)
  assert a == expect_out



def test_pandasSets_sameIndex():
  from isitfit.utils import pd_series_frozenset_union
  import pandas as pd

  fset = frozenset
  s1=pd.Series([fset([1]), fset([1,2])])
  s2=pd.Series([fset([1]), fset([1,3])])
  a = pd_series_frozenset_union(s1, s2)
  e = pd.DataFrame({'a3': [fset([1]), fset([1,2,3])]})
  pd.testing.assert_series_equal(a, e.a3)


def test_pandasSets_differentIndex():
  from isitfit.utils import pd_series_frozenset_union
  import pandas as pd

  fset = frozenset
  s1=pd.Series([fset([1]), fset([1,2])], index=[0,1])
  s2=pd.Series([fset([1])], index=[0])
  actual = pd_series_frozenset_union(s1, s2)
  expected = pd.DataFrame({'a3': [fset([1]), fset([1,2])]})
  pd.testing.assert_series_equal(actual, expected.a3)



from isitfit.utils import AwsProfileMan
class TestAwsProfileMan:
  def test_init(self):
    pm = AwsProfileMan()
    assert True # no exception

  def test_validateProfile(self):
    class MockClickCtx:
      obj = {
      }

    click_ctx = MockClickCtx()

    pm = AwsProfileMan()
    actual = pm.validate_profile(click_ctx, "profile", "default")
    assert actual=="default"

    import click
    with pytest.raises(click.BadParameter):
      pm.validate_profile(click_ctx, "profile", "inexistant")


  def test_prompt(self):
    pm = AwsProfileMan()
    x = pm.prompt()
    assert x is not None



# get fixture
from isitfit.tests.cli.test_clickDescendents import ping_matomo

# test functions using above fixture
class TestPromptToEmailIfNotRequested:

  def test_ok(self, ping_matomo):
    """
    No need for click.command here as this will never reach the click.prompt line
    """
    from isitfit.utils import PromptToEmailIfNotRequested
    pte = PromptToEmailIfNotRequested()
    import tempfile
    with tempfile.NamedTemporaryFile() as fh:
      pte.last_email_cl.fn = fh.name # overwrite file to save last-used email
      expected = 'me@example.com'
      actual = pte.prompt(expected)
      assert actual == expected


  def test_oneInputNoLast(self, ping_matomo):
    """
    # build a fake click command so that the click.prompt will be emulated
    # https://click.palletsprojects.com/en/7.x/testing/?highlight=test#input-streams
    """
    import click
    @click.command()
    def cmd():
      from isitfit.utils import PromptToEmailIfNotRequested
      pte = PromptToEmailIfNotRequested()
      import tempfile
      with tempfile.NamedTemporaryFile() as fh:
        pte.last_email_cl.fn = fh.name # overwrite file to save last-used email
        pte.prompt(None)

    # trigger
    from click.testing import CliRunner
    runner = CliRunner()
    result = runner.invoke(cmd, input='me@example.com\n')
    print(result.__dict__) # in case of exception, this will show details
    assert not result.exception
    assert '[skip]' in result.output


  def test_oneInputSetLast(self, ping_matomo):
    """
    # build a fake click command so that the click.prompt will be emulated
    # https://click.palletsprojects.com/en/7.x/testing/?highlight=test#input-streams
    """
    import click
    @click.command()
    def cmd():
      from isitfit.utils import PromptToEmailIfNotRequested
      pte = PromptToEmailIfNotRequested()
      import tempfile
      with tempfile.NamedTemporaryFile() as fh:
        pte.last_email_cl.fn = fh.name # overwrite file to save last-used email
        pte.last_email_cl.set('me@example.com')
        pte.prompt(None)

    # trigger
    from click.testing import CliRunner
    runner = CliRunner()
    result = runner.invoke(cmd, input='\n')
    print(result.__dict__) # in case of exception, this will show details
    assert not result.exception
    assert '[skip]' not in result.output
    assert '[me@example.com]' in result.output


  def test_userInput(self):
    import click
    from click.testing import CliRunner

    class MyWrap:
      def dummyFac(self, emailIn, emailPrompt):
        self.emailOut = None

        @click.command()
        def dummyCmd():
          from isitfit.utils import PromptToEmailIfNotRequested
          pte = PromptToEmailIfNotRequested()
          import tempfile
          with tempfile.NamedTemporaryFile() as fh:
            pte.last_email_cl.fn = fh.name # overwrite file to save last-used email
            # dont set to leave blank # pte.last_email_cl.set('me@example.com')
            self.emailOut = pte.prompt(emailIn)

        # https://stackoverflow.com/q/38143366/4126114
        runner = CliRunner()
        result = runner.invoke(dummyCmd, input=emailPrompt)
        return self.emailOut

    mw = MyWrap()
    actual = mw.dummyFac(None, '\n')
    assert actual is None
    actual = mw.dummyFac(None, 'n\n')
    assert actual is None
    actual = mw.dummyFac(None, 'y\nshadi@abc.com')
    assert actual == ['shadi@abc.com']
    actual = mw.dummyFac(None, 'y\nbla\nshadi@abc.com')
    assert actual == ['shadi@abc.com']





def test_word2color():
  from isitfit.utils import Word2Color
  w2c = Word2Color()
  actual = w2c.convert('whatever')
  assert actual=='green'

  actual = w2c.convert('heay')
  assert actual=='grey'

  actual = w2c.convert('another-word_under')
  assert actual=='grey'

  actual = w2c.convert('yih')
  assert actual=='cyan'


def test_pdSubsetLatest():
  import pandas as pd
  df_in = pd.DataFrame(
    {
      'a':  [1, 2, 3, 4, 5, 6, 7, 8, 9,10,11,12,13],
      'b':  [1, 1, 1, 2, 2, 2, 1, 1, 1, 2, 2, 2, 2],
    },
    index = [1, 2, 3, 4, 5, 6, 7, 8, 9,10,11,12,13]
  )
  df_expected = pd.DataFrame(
    {
      'a':  [10,11,12,13],
      'b':  [ 2, 2, 2, 2]
    },
    index = [10,11,12,13]
  )

  from isitfit.utils import pd_subset_latest
  df_actual = pd_subset_latest(df_in, 'b', 'a')

  pd.testing.assert_frame_equal(df_actual, df_expected)
  assert len(set(df_actual.b.to_list())) == 1
