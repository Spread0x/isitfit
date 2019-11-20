def ec2_cost_analyze(ctx, filter_tags):
    # moved these imports from outside the function to inside it so that `isitfit --version` wouldn't take 5 seconds due to the loading
    from isitfit.cost.mainManager import MainManager
    from isitfit.cost.cloudtrail_ec2type import CloudtrailCached
    from isitfit.cost.ec2.calculator_analyze import CalculatorAnalyzeEc2
    from isitfit.cost.cacheManager import RedisPandas as RedisPandasCacheManager
    from isitfit.cost.datadogManager import DatadogCached
    from isitfit.cost.ec2TagFilter import Ec2TagFilter
    from isitfit.cost.redshift.cloudwatchman import CloudwatchEc2
    from isitfit.cost.ec2.reporter import ReporterAnalyzeEc2
    from isitfit.ec2_catalog import Ec2Catalog
    from isitfit.cost.ec2.ec2Common import Ec2Common
    from isitfit.cost.redshift.iterator import Ec2Iterator


    share_email = ctx.obj.get('share_email', None)
    ul = CalculatorAnalyzeEc2(ctx)

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

    return mm


def ec2_cost_optimize(ctx, n, filter_tags):
    # moved these imports from outside the function to inside it so that `isitfit --version` wouldn't take 5 seconds due to the loading
    from isitfit.cost.mainManager import MainManager
    from isitfit.cost.cloudtrail_ec2type import CloudtrailCached
    from isitfit.cost.ec2.calculator_optimize import CalculatorOptimizeEc2
    from isitfit.cost.cacheManager import RedisPandas as RedisPandasCacheManager
    from isitfit.cost.datadogManager import DatadogCached
    from isitfit.cost.ec2TagFilter import Ec2TagFilter
    from isitfit.cost.redshift.cloudwatchman import CloudwatchEc2
    from isitfit.cost.ec2.reporter import ReporterOptimizeEc2
    from isitfit.ec2_catalog import Ec2Catalog
    from isitfit.cost.ec2.ec2Common import Ec2Common
    from isitfit.cost.redshift.iterator import Ec2Iterator

    ol = CalculatorOptimizeEc2(n)

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

    return mm
