import logging
logger = logging.getLogger('isitfit')

import click

# Use "cls" to use the IsitfitCommand class to show the footer
# https://github.com/pallets/click/blob/8df9a6b2847b23de5c65dcb16f715a7691c60743/click/decorators.py#L92
from ..utils import IsitfitCommand


@click.group(help="Evaluate AWS EC2 costs", invoke_without_command=False)
@click.pass_context
def cost(ctx):
  pass




@cost.command(help='Analyze AWS EC2 cost', cls=IsitfitCommand)
@click.option('--filter-tags', default=None, help='filter instances for only those carrying this value in the tag name or value')
@click.pass_context
def analyze(ctx, filter_tags):
    # gather anonymous usage statistics
    from ..utils import ping_matomo, IsitfitCliError
    ping_matomo("/cost/analyze")

    #logger.info("Is it fit?")
    logger.info("Initializing...")

    # moved these imports from outside the function to inside it so that `isitfit --version` wouldn't take 5 seconds due to the loading
    from ..cost.mainManager import MainManager
    from ..cost.utilizationListener import UtilizationListener
    from ..cost.optimizerListener import OptimizerListener
    from ..cost.datadogManager import DatadogManager

    share_email = ctx.obj.get('share_email', None)
    ul = UtilizationListener(share_email, ctx)
    ddg = DatadogManager()
    mm = MainManager(ctx, ddg, filter_tags)

    # utilization listeners
    mm.add_listener('ec2', ul.per_ec2)
    mm.add_listener('all', ul.after_all)
    mm.add_listener('all', ul.display_all)
    mm.add_listener('all', ul.share_email)

    # start download data and processing
    logger.info("Fetching history...")
    mm.get_ifi()


@cost.command(help='Generate recommendations of optimal EC2 sizes', cls=IsitfitCommand)
@click.option('--n', default=0, help='number of underused ec2 optimizations to find before stopping. Skip to get all optimizations')
@click.option('--filter-tags', default=None, help='filter instances for only those carrying this value in the tag name or value')
@click.pass_context
def optimize(ctx, n, filter_tags):
    # gather anonymous usage statistics
    from ..utils import ping_matomo, IsitfitCliError
    ping_matomo("/cost/optimize")

    #logger.info("Is it fit?")
    logger.info("Initializing...")

    # moved these imports from outside the function to inside it so that `isitfit --version` wouldn't take 5 seconds due to the loading
    from ..cost.mainManager import MainManager
    from ..cost.utilizationListener import UtilizationListener
    from ..cost.optimizerListener import OptimizerListener
    from ..cost.datadogManager import DatadogManager

    ol = OptimizerListener(n)
    ddg = DatadogManager()
    mm = MainManager(ctx, ddg, filter_tags)

    # utilization listeners
    mm.add_listener('pre', ol.handle_pre)
    mm.add_listener('ec2', ol.per_ec2)
    mm.add_listener('all', ol.after_all)
    mm.add_listener('all', ol.storecsv_all)
    mm.add_listener('all', ol.display_all)


    # start download data and processing
    logger.info("Fetching history...")
    mm.get_ifi()

