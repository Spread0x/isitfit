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

    logger.info("Calculating the Cost-Weighted Average Utilization (CWAU) of the AWS EC2 account:")
    logger.info("Fetching history...")
    mm = MainManager()
    n_ec2, sum_capacity, sum_used, cwau = mm.get_ifi()
    logger.info("... done")
    logger.info("")
    logger.info("Summary:")
    logger.info("Number of EC2 machines = %i"%n_ec2)
    logger.info("Billed cost per hour = %0.2f $/hour"%sum_capacity)
    logger.info("Used cost per hour = %0.2f $/hour"%sum_used)
    logger.info("CWAU = Used / Billed * 100 = %0.0f %%"%cwau)
    logger.info("")
    logger.info("For reference:")
    logger.info("* CWAU >= 70% is well optimized")
    logger.info("* CWAU <= 30% is underused")
    logger.info("* CWAU in isitfit version 0.1.2 is based on CPU utilization only (and not memory utilization)")


if __name__ == '__main__':
  cli()
