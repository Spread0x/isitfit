from .. import isitfit_version
import click

def version_core():
  print('isitfit version %s'%isitfit_version)

# Do not use the IsitfitCommand class to show the footer
# because the user will see the version info multiple times
@click.command(help="Show isitfit version")
def version():
  # This is redundant with isitfit --version (just in case a user calls "isitfit version")
  # The idea is similar to `git version` and `git --version`
  version_core()
  return


