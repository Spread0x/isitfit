from .. import isitfit_version
import click

def version_core():
  print('isitfit version %s'%isitfit_version)

@click.command(help="Show isitfit version")
def version():
  # This is redundant with isitfit --version (just in case a user calls "isitfit version")
  # The idea is similar to `git version` and `git --version`
  version_core()
  return


