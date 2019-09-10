# RuntimeError: Click will abort further execution because Python 3 was configured to use ASCII as encoding for the environment. 
# Consult https://click.palletsprojects.com/en/7.x/python3/ for mitigation steps.
from gitRemoteAws.utils import mysetlocale
mysetlocale()


import logging
logger = logging.getLogger('isitfit')

from .mainManager import MainManager
import click
from tabulate import tabulate

from . import isitfit_version

@click.command()
@click.option('--debug', is_flag=True)
@click.option('--version', is_flag=True)
def cli(debug, version):

    if version:
      print('isitfit version %s'%isitfit_version)
      return

    logLevel = logging.DEBUG if debug else logging.INFO
    ch = logging.StreamHandler()
    ch.setLevel(logLevel)
    logger.addHandler(ch)
    logger.setLevel(logLevel)

    logger.info("Is it fit?")
    logger.info("Cost-Weighted Average Utilization (CWAU) of the AWS EC2 account:")
    logger.info("Fetching history...")
    mm = MainManager()
    n_ec2, sum_capacity, sum_used, cwau = mm.get_ifi()
    logger.info("... done")
    
    dt_start = mm.StartTime.strftime("%Y-%m-%d")
    dt_end   = mm.EndTime.strftime("%Y-%m-%d")
    
    table = [
      ["Analysis start date", "%s"%dt_start],
      ["Analysis end date", "%s"%dt_end],
      ["Number of EC2 machines", "%i"%n_ec2],
      ["Billed cost", "%0.2f $"%sum_capacity],
      ["Used cost", "%0.2f $"%sum_used],
      ["CWAU = Used / Billed * 100", "%0.0f %%"%cwau],
    ]
    
    logger.info("")
    logger.info("Summary:")
    logger.info("")
    logger.info(tabulate(table, headers=['Field', 'Value']))
    logger.info("")
    logger.info("For reference:")
    logger.info("* CWAU >= 70% is well optimized")
    logger.info("* CWAU <= 30% is underused")
    logger.info("* isitfit version %s is based on CPU utilization only (and not yet on memory utilization)"%isitfit_version)


if __name__ == '__main__':
  cli()
