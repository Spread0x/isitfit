from isitfit.utils import logger


import click

# Use "cls" to use the IsitfitCommand class to show the footer
# https://github.com/pallets/click/blob/8df9a6b2847b23de5c65dcb16f715a7691c60743/click/decorators.py#L92
from isitfit.cli.click_descendents import IsitfitCommand, isitfit_group, isitfit_option_base, isitfit_option_profile


@isitfit_group(help="Evaluate AWS EC2 costs", invoke_without_command=False)
@click.option('--filter-region', default=None, help='specify a single region against which to run cost analysis/optimization')
@isitfit_option_profile()
@isitfit_option_base(
  '--ndays',
  default=7,
  prompt='Number of days to lookback (between 1 and 90, use `isitfit cost --ndays=7 ...` to skip this prompt)',
  help='number of days to look back in the data history',
  type=click.IntRange(1, 90)
)
@click.pass_context
def cost(ctx, filter_region, ndays, profile):
  # FIXME click bug: `isitfit command subcommand --help` is calling the code in here. Workaround is to check --help and skip the whole section
  import sys
  if '--help' in sys.argv: return

  # gather anonymous usage statistics
  from isitfit.utils import ping_matomo
  ping_matomo("/cost?filter_region=%s&ndays=%i"%(filter_region, ndays))

  # save to click context
  ctx.obj['ndays'] = ndays
  ctx.obj['filter_region'] = filter_region

  pass



# Check note above about ndays
# Another note about ndays: using click.IntRange for validation. Ref: https://click.palletsprojects.com/en/7.x/options/?highlight=prompt#range-options
@cost.command(help='Analyze AWS EC2 cost', cls=IsitfitCommand)
@click.option('--filter-tags', default=None, help='filter instances for only those carrying this value in the tag name or value')
@click.option('--save-details', is_flag=True, help='Save details behind calculations to CSV files')
@click.pass_context
def analyze(ctx, filter_tags, save_details):
    # gather anonymous usage statistics
    from isitfit.utils import ping_matomo, b2l
    ping_matomo("/cost/analyze?filter_tags=%s&save_details=%s"%(filter_tags, b2l(save_details) ))

    # save to click context
    share_email = ctx.obj.get('share_email', [])

    #logger.info("Is it fit?")
    logger.info("Initializing...")


    # set up pipelines for ec2, redshift, and aggregator
    from isitfit.cost import ec2_cost_analyze, redshift_cost_analyze, account_cost_analyze
    mm_eca = ec2_cost_analyze(ctx, filter_tags, save_details)
    mm_rca = redshift_cost_analyze(share_email, filter_region=ctx.obj['filter_region'], ctx=ctx, filter_tags=filter_tags)

    # combine the 2 pipelines into a new pipeline
    mm_all = account_cost_analyze(mm_eca, mm_rca, ctx, share_email)

    # configure tqdm
    from isitfit.tqdmman import TqdmL2Quiet
    tqdml2 = TqdmL2Quiet(ctx)

    # Run pipeline
    mm_all.get_ifi(tqdml2)


@cost.command(help='Generate recommendations of optimal EC2 sizes', cls=IsitfitCommand)
@click.option('--n', default=-1, help='number of underused ec2 optimizations to find before stopping. Skip to get all optimizations')
@click.option('--filter-tags', default=None, help='filter instances for only those carrying this value in the tag name or value')
@click.pass_context
def optimize(ctx, n, filter_tags):
    # gather anonymous usage statistics
    from isitfit.utils import ping_matomo
    ping_matomo("/cost/optimize?n=%i&filter_tags=%s"%(n, filter_tags ))

    # save to context
    share_email = ctx.obj.get('share_email', [])

    #logger.info("Is it fit?")
    logger.info("Initializing...")

    from isitfit.cost import ec2_cost_optimize, redshift_cost_optimize, account_cost_optimize
    mm_eco = ec2_cost_optimize(ctx, n, filter_tags)
    mm_rco = redshift_cost_optimize(filter_region=ctx.obj['filter_region'], ctx=ctx, filter_tags=filter_tags)

    # merge and run pipelines
    mm_all = account_cost_optimize(mm_eco, mm_rco, ctx)

    # configure tqdm
    from isitfit.tqdmman import TqdmL2Quiet
    tqdml2 = TqdmL2Quiet(ctx)

    # Run pipeline
    mm_all.get_ifi(tqdml2)
