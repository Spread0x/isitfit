from .. import isitfit_version
import click

def version_core():
  print('isitfit version %s'%isitfit_version)


# Do not use the IsitfitCommand class to show the footer
# because the user will see the version info multiple times
@click.command(help="Show isitfit version")
def version():
  # gather anonymous usage statistics
  from isitfit.utils import ping_matomo
  ping_matomo("/version")

  version_core()
  return


