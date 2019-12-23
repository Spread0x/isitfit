"""
General tests for click usage. Check each test's docstrings for more details
"""

import click

class TestClickOptionMultipleWithDefault:
  """
  General tests for click to check how it deals with defaults and multiple=True (for share-email option)
  The goal is to figure out when to *not* prompt the user for an email even if it is not passed
  In other words, finding a signal about the difference between --share-email empty because not passed or --share-email empty because intended

  Conclusion: click doesn't offer such a signal without adding a separate option --skip-share-email
  """
  def test_multipleWithDefault(self):
    # do not set default, do not pass on CLI
    @click.command()
    @click.option('--share-email', multiple=True, help='Share result to email address')
    def doit_defaultNo(share_email):
      assert type(share_email) is tuple
      assert len(share_email)==0

    from click.testing import CliRunner
    runner = CliRunner()

    result = runner.invoke(doit_defaultNo, [], input='\n')
    assert not result.exception


    # set default to None, do not pass on CLI
    @click.command()
    @click.option('--share-email', multiple=True, help='Share result to email address', default=None)
    def doit_defaultYes(share_email):
      assert share_email is not None # despite the default
      assert type(share_email) is tuple
      assert len(share_email)==0

    from click.testing import CliRunner
    runner = CliRunner()

    result = runner.invoke(doit_defaultYes, [], input='\n')
    assert not result.exception


    # set default to None, pass some input on CLI
    e1, e2 = 'e1@foo.com', 'e2@bla.com'

    # set default to None, pass arguments on CLI
    @click.command()
    @click.option('--share-email', multiple=True, help='Share result to email address', default=None)
    def doit_defaultYes(share_email):
      assert type(share_email) is tuple
      assert len(share_email)==2
      assert share_email == (e1, e2)

    from click.testing import CliRunner
    runner = CliRunner()

    result = runner.invoke(doit_defaultYes, [ f'--share-email={e1}', f'--share-email={e2}' ], input='\n')
    assert not result.exception


    # do not set default, do not pass on CLI, add option to skip
    @click.command()
    @click.option('--share-email', multiple=True, help='Share result to email address')
    @click.option('--skip-prompt-email', is_flag=True, help='Skip the prompt to share result to email address')
    def doit_defaultNo(share_email, skip_prompt_email):
      assert type(share_email) is tuple
      assert len(share_email)==0
      assert skip_prompt_email

    from click.testing import CliRunner
    runner = CliRunner()

    result = runner.invoke(doit_defaultNo, ['--skip-prompt-email'], input='\n')
    assert not result.exception


