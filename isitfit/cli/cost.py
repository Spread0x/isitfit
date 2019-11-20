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

    # moved these imports from outside the function to inside it so that `isitfit --version` wouldn't take 5 seconds due to the loading
    from ..cost.mainManager import MainManager
    from ..cost.cloudtrail_ec2type import CloudtrailCached
    from ..cost.utilizationListener import UtilizationListener
    from ..cost.cacheManager import RedisPandas as RedisPandasCacheManager
    from ..cost.datadogManager import DatadogCached
    from ..cost.ec2TagFilter import Ec2TagFilter
    from isitfit.cost.redshift.cloudwatchman import CloudwatchEc2
    from isitfit.cost.ec2.reporter import ReporterAnalyzeEc2
    from isitfit.ec2_catalog import Ec2Catalog
    from isitfit.cost.ec2.ec2Common import Ec2Common
    from isitfit.cost.redshift.iterator import Ec2Iterator


    share_email = ctx.obj.get('share_email', None)
    ul = UtilizationListener(ctx)

    # manager of redis-pandas caching
    cache_man = RedisPandasCacheManager()

    ddg = DatadogCached(cache_man)
    etf = Ec2TagFilter(filter_tags)
    cloudwatchman = CloudwatchEc2(cache_man)
    ra = ReporterAnalyzeEc2()
    mm = MainManager(ctx)
    ec2_cat = Ec2Catalog()
    ec2_common = Ec2Common()
    ec2_it = Ec2Iterator(filter_region=ctx.obj['filter_region'])

    # boto3 cloudtrail data
    cloudtrail_manager = CloudtrailCached(mm.EndTime, cache_man)

    # update dict and return it
    # https://stackoverflow.com/a/1453013/4126114
    inject_email_in_context = lambda context_all: dict({'emailTo': share_email}, **context_all)
    inject_analyzer = lambda context_all: dict({'analyzer': ul}, **context_all)

    # utilization listeners
    mm.set_iterator(ec2_it)
    mm.add_listener('pre', cache_man.handle_pre)
    mm.add_listener('pre', cloudtrail_manager.init_data)
    mm.add_listener('pre', ec2_cat.handle_pre)
    mm.add_listener('ec2', etf.per_ec2)
    mm.add_listener('ec2', cloudwatchman.per_ec2)
    mm.add_listener('ec2', cloudtrail_manager.single)
    mm.add_listener('ec2', ec2_common._handle_ec2obj)
    mm.add_listener('ec2', ddg.per_ec2)
    mm.add_listener('ec2', ul.per_ec2)
    mm.add_listener('all', ec2_common.after_all)
    mm.add_listener('all', ul.after_all)
    mm.add_listener('all', inject_analyzer)
    mm.add_listener('all', ra.postprocess)
    mm.add_listener('all', ra.display)
    mm.add_listener('all', inject_email_in_context)
    mm.add_listener('all', ra.email)

    # start download data and processing
    logger.info("Fetching history...")
    mm.get_ifi()

    # -----------------------------
    # now analyze redshift clusters
    logger.info("")
    logger.info("-"*20)
    from ..cost.redshift.cli import cost_analyze
    cost_analyze(share_email, filter_region=ctx.obj['filter_region'])
    logger.info("-"*20)



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

    # moved these imports from outside the function to inside it so that `isitfit --version` wouldn't take 5 seconds due to the loading
    from ..cost.mainManager import MainManager
    from ..cost.cloudtrail_ec2type import CloudtrailCached
    from ..cost.optimizerListener import OptimizerListener
    from ..cost.cacheManager import RedisPandas as RedisPandasCacheManager
    from ..cost.datadogManager import DatadogCached
    from ..cost.ec2TagFilter import Ec2TagFilter
    from isitfit.cost.redshift.cloudwatchman import CloudwatchEc2
    from isitfit.cost.ec2.reporter import ReporterOptimizeEc2
    from isitfit.ec2_catalog import Ec2Catalog
    from isitfit.cost.ec2.ec2Common import Ec2Common
    from isitfit.cost.redshift.iterator import Ec2Iterator

    ol = OptimizerListener(n)

    # manager of redis-pandas caching
    cache_man = RedisPandasCacheManager()

    ddg = DatadogCached(cache_man)
    etf = Ec2TagFilter(filter_tags)
    cloudwatchman = CloudwatchEc2(cache_man)
    ra = ReporterOptimizeEc2()
    mm = MainManager(ctx)
    ec2_cat = Ec2Catalog()
    ec2_common = Ec2Common()
    ec2_it = Ec2Iterator(filter_region=ctx.obj['filter_region'])

    # boto3 cloudtrail data
    cloudtrail_manager = CloudtrailCached(mm.EndTime, cache_man)

    # update dict and return it
    # https://stackoverflow.com/a/1453013/4126114
    inject_analyzer = lambda context_all: dict({'analyzer': ol}, **context_all)

    # utilization listeners
    mm.set_iterator(ec2_it)
    mm.add_listener('pre', cache_man.handle_pre)
    mm.add_listener('pre', cloudtrail_manager.init_data)
    mm.add_listener('pre', ol.handle_pre)
    mm.add_listener('pre', ec2_cat.handle_pre)
    mm.add_listener('ec2', etf.per_ec2)
    mm.add_listener('ec2', cloudwatchman.per_ec2)
    mm.add_listener('ec2', cloudtrail_manager.single)
    mm.add_listener('ec2', ec2_common._handle_ec2obj)
    mm.add_listener('ec2', ddg.per_ec2)
    mm.add_listener('ec2', ol.per_ec2)
    mm.add_listener('all', ec2_common.after_all)
    mm.add_listener('all', inject_analyzer)
    mm.add_listener('all', ra.postprocess)
    mm.add_listener('all', ra.display)


    # start download data and processing
    logger.info("Fetching history...")
    mm.get_ifi()

    # -----------------------------
    # now optimize redshift clusters
    logger.info("")
    logger.info("-"*20)
    from ..cost.redshift.cli import cost_optimize
    cost_optimize(filter_region=ctx.obj['filter_region'])
    logger.info("-"*20)

