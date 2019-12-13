#import pytest
#
#
# WORK IN PROGRESS
#
#def test_issue9():
#    # prepare
#
#    # build a fake click command so that the click.prompt will be emulated
#    # https://click.palletsprojects.com/en/7.x/testing/?highlight=test#input-streams
#    import click
#    @click.command()
#    def cmd():
#      dataType = 'cost analyze (binned)'
#      import pandas as pd
#      dataVal = pd.DataFrame()
#      from isitfit.cli.core import cli_core
#      from ..emailMan import EmailMan
#      em = EmailMan(None, None, None)
#      em.send([])
#
#    # trigger
#    from click.testing import CliRunner
#    runner = CliRunner()
#    result = runner.invoke(sendemail_cmd, [], input='\n')
#    print(result.__dict__) # in case of exception, this will show details
#    assert not result.exception
#    assert True # no exception
#
