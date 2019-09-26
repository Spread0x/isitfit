def mergeSeriesOnTimestampRange(df_cpu, df_type):
  """
  Upsamples df_type to df_cpu.
  Example:
    Input
      df_cpu = pd.Series({'time': [1,2,3,4], 'field_1': [5,6,7,8]})
      df_type = pd.Series({'time': [1,3], 'field_2': ['a','b']})
    Returns
      pd.Series({'time': [1,2,3,4], 'field_1': [5,6,7,8], 'field_2': ['a','a','b','b']})
  """
  import numpy as np

  df_cpu['instanceType'] = None
  # assume df_type is sorted in decreasing EventTime order (very important)
  # NB: since some instances are not present in the cloudtrail (for which we append artificially the "now" type)
  #     Need to traverse the df_type matrix backwards
  for index, row_type in df_type.iterrows():
      # use row_type.name instead of row_type['EventTime']
      # check note above about needing to traverse backwards
      # df_cpu.iloc[np.where(df_cpu.Timestamp >= row_type.name)[0], df_cpu.columns.get_loc('instanceType')] = row_type['instanceType']
      df_cpu.iloc[np.where(df_cpu.Timestamp <= row_type.name)[0], df_cpu.columns.get_loc('instanceType')] = row_type['instanceType']

  # fill na at beginning with back-fill
  # (artifact of cloudwatch having data at days before the creation of the instance)
  df_cpu['instanceType'] = df_cpu['instanceType'].fillna(method='backfill')
  return df_cpu







def ec2_catalog():
    import requests
    from cachecontrol import CacheControl
    from cachecontrol.caches.file_cache import FileCache

    import logging
    logger = logging.getLogger('isitfit')
    logger.debug("Downloading ec2 catalog (cached to local file)")

    # based on URL = 'http://www.ec2instances.info/instances.json'
    # URL = 's3://...csv'
    # Edit 2019-09-10 use CDN link instead of direct gitlab link
    # URL = 'https://gitlab.com/autofitcloud/www.ec2instances.info-ec2op/raw/master/www.ec2instances.info/t3b_smaller_familyL2.json'
    URL = 'https://cdn.jsdelivr.net/gh/autofitcloud/www.ec2instances.info-ec2op/www.ec2instances.info/t3b_smaller_familyL2.json'

    # cached https://cachecontrol.readthedocs.io/en/latest/
    sess = requests.session()
    cached_sess = CacheControl(sess, cache=FileCache('/tmp/isitfit_ec2info.cache'))
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
    return df


# copied from git-remote-aws
def mysetlocale():
  li = 'en_US.utf8'
  import os
  os.environ["LC_ALL"] = li
  os.environ["LANG"]   = li

