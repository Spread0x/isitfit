class Ec2Catalog:
  """
  download ec2 catalog: 2 columns: ec2 type, ec2 cost per hour
  """

  def handle_pre(self, context_pre):
    import requests
    from cachecontrol import CacheControl
    from cachecontrol.caches.file_cache import FileCache

    from isitfit.utils import logger
    
    logger.debug("Downloading ec2 catalog (cached to local file)")

    # based on URL = 'http://www.ec2instances.info/instances.json'
    # URL = 's3://...csv'
    # Edit 2019-09-10 use CDN link instead of direct gitlab link
    # URL = 'https://gitlab.com/autofitcloud/www.ec2instances.info-ec2op/raw/master/www.ec2instances.info/t3b_smaller_familyL2.json'
    URL = 'https://cdn.jsdelivr.net/gh/autofitcloud/www.ec2instances.info-ec2op/www.ec2instances.info/t3b_smaller_familyL2.json'

    # Update 2019-12-03: move into /tmp/isitfit/
    # fc_dir = '/tmp/isitfit_ec2info.cache'
    from isitfit.dotMan import DotMan
    import os
    fc_dir = os.path.join(DotMan().tempdir(), 'ec2info.cache')

    # cached https://cachecontrol.readthedocs.io/en/latest/
    sess = requests.session()
    cached_sess = CacheControl(sess, cache=FileCache(fc_dir))
    r = cached_sess.request('get', URL)

    # read catalog, copy from ec2op-cli/ec2op/optimizer/cwDailyMaxMaxCpu
    import json
    j = json.dumps(r.json(), indent=4, sort_keys=True)
    from pandas import read_json
    df = read_json(j, orient='split')
    
    # Edit 2019-09-13 no need to subsample the columns at this stage
    # df = df[['API Name', 'Linux On Demand cost']]

    df = df.rename(columns={'Linux On Demand cost': 'cost_hourly'})
    # df = df.set_index('API Name') # need to use merge, not index
    context_pre['df_cat'] = df

    return context_pre

