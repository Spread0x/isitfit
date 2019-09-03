# RuntimeError: Click will abort further execution because Python 3 was configured to use ASCII as encoding for the environment. 
# Consult https://click.palletsprojects.com/en/7.x/python3/ for mitigation steps.
from gitRemoteAws.utils import mysetlocale
mysetlocale()


import logging
logger = logging.getLogger('isitfit')

from .mainManager import MainManager


import click

@click.command()
@click.option('--debug', is_flag=True)
def cli(debug):
    logLevel = logging.DEBUG if debug else logging.INFO
    ch = logging.StreamHandler()
    ch.setLevel(logLevel)
    logger.addHandler(ch)
    logger.setLevel(logLevel)

    mm = MainManager()
    ifi = mm.get_ifi()
    logger.info("IFI = %0.2f%%"%ifi)
    logger.info("(IFI >= 70% is well optimized)")
    logger.info("(IFI <= 30% is underused)")


if __name__ == '__main__':
  cli()
