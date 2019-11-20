import logging
logger = logging.getLogger('isitfit')

import click

# Use "cls" to use the IsitfitCommand class to show the footer
# https://github.com/pallets/click/blob/8df9a6b2847b23de5c65dcb16f715a7691c60743/click/decorators.py#L92
from ..utils import IsitfitCommand


@click.group(help="Evaluate AWS EC2 costs", invoke_without_command=False)
@click.option('--filter-region', default=None, help='specify a single region against which to run cost analysis/optimization')
@click.pass_context
def cost(ctx, filter_region):
  ctx.obj['filter_region'] = filter_region
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

    share_email = ctx.obj.get('share_email', None)

    from isitfit.cost.ec2.pipeline_factory import ec2_cost_analyze
    from isitfit.cost.redshift.pipeline_factory import redshift_cost_analyze
    mm_eca = ec2_cost_analyze(ctx, filter_tags)
    mm_rca = redshift_cost_analyze(share_email, filter_region=ctx.obj['filter_region'])

    # start download data and processing
    logger.info("Fetching history: EC2...")
    mm_eca.get_ifi()
    logger.info("Fetching history: Redshift...")
    mm_rca.get_ifi()

    # Display results
    #logger.info("")
    #logger.info("-"*20)
    #logger.info("-"*20)




@cost.command(help='Generate recommendations of optimal EC2 sizes', cls=IsitfitCommand)
@click.option('--n', default=-1, help='number of underused ec2 optimizations to find before stopping. Skip to get all optimizations')
@click.option('--filter-tags', default=None, help='filter instances for only those carrying this value in the tag name or value')
@click.pass_context
def optimize(ctx, n, filter_tags):
    # gather anonymous usage statistics
    from ..utils import ping_matomo, IsitfitCliError
    ping_matomo("/cost/optimize")

    #logger.info("Is it fit?")
    logger.info("Initializing...")

    from isitfit.cost.ec2.pipeline_factory import ec2_cost_optimize
    from isitfit.cost.redshift.pipeline_factory import redshift_cost_optimize
    mm_eco = ec2_cost_optimize(ctx, n, filter_tags)
    mm_rco = redshift_cost_optimize(filter_region=ctx.obj['filter_region'])

    # start download data and processing
    logger.info("Fetching history: EC2...")
    mm_eco.get_ifi()
    logger.info("Fetching history: Redshift...")
    mm_rco.get_ifi()

    # -----------------------------
    # Display results
    #logger.info("")
    #logger.info("-"*20)
    #logger.info("-"*20)

