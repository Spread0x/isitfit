"""
Functional tests run on shadi@autofitcloud.com AWS account
"""

from isitfit.cost.cloudtrail_iterator import *
import pandas as pd
pd.set_option("display.max_columns", 10)
pd.set_option("display.width", None)

# variables for tests below
region_include = ['us-west-1', 'us-west-2', 'us-east-1', 'us-east-2']
from tqdm import tqdm as tqdmman

cache_man = None

EndTime = 'end time'
ec2_instances = [
  ( { 'Region': 'us-west-1',
      'ServiceName': 'ec2',
      'InstanceType': 't2.large',
      'InstanceId': 'i-1234'
    },
    'i-1234',
    None,
    None
  ),
  ( { 'Region': 'us-west-1',
      'ServiceName': 'redshift',
      'NodeType': 'dc2.large',
      'NumberOfNodes': 3,
      'ClusterIdentifier': 'test-1234'
    },
    'test-1234',
    None,
    None
  ),
]


import os 
BASEDIR = os.path.dirname(os.path.realpath(__file__))

# start of tests
def test_oneregion():
    # get all data and compare
    df_one = EventAggregatorOneRegion().get()
    assert not df_one.EventName.isnull().values.any()

    #print("")
    #print("one region")
    #print(df_one)

    fix_fn = "fixture_cloudtrailIterator_oneRegion_AutofitCloud-shadi_20191202.pkl"
    fix_fn = os.path.join(BASEDIR, fix_fn)
    # df_one.to_pickle(fix_fn)
    df_exp = pd.read_pickle(fix_fn)

    pd.testing.assert_frame_equal(df_exp, df_one)


def test_allregions():
    df_all = EventAggregatorAllRegions(region_include, tqdmman).get()

    print("")
    print("all regions")
    print(df_all)

    fix_fn = "fixture_cloudtrailIterator_allRegions_AutofitCloud-shadi_20191202.pkl"
    fix_fn = os.path.join(BASEDIR, fix_fn)
    #df_all.to_pickle(fix_fn)
    df_exp = pd.read_pickle(fix_fn)

    pd.testing.assert_frame_equal(df_exp, df_all)


def test_cached():
    # set up cache
    from isitfit.cost.cacheManager import RedisPandas
    cm = RedisPandas()

    # set up main class, and use a test cache key
    eac = EventAggregatorCached(region_include, tqdmman, cm)
    eac.cache_key = 'cloudtrail_iterator.test'

    # delete the key if used
    assert cm.isSetup()
    cm.connect()
    cm.redis_client.delete(eac.cache_key)

    # get pandas dataframe
    df_cached = eac.get()
    print("")
    print("cached")
    print(df_cached)

    # expect same file as un-cached
    fix_fn = "fixture_cloudtrailIterator_allRegions_AutofitCloud-shadi_20191202.pkl"
    fix_fn = os.path.join(BASEDIR, fix_fn)
    df_exp = pd.read_pickle(fix_fn)

    pd.testing.assert_frame_equal(df_exp, df_cached)



def test_postprocessed():
    df_post = EventAggregatorPostprocessed(region_include, tqdmman, cache_man, EndTime).get(ec2_instances, 2)

    print("")
    print("post-processed")
    print(df_post)

    fix_fn = "fixture_cloudtrailIterator_postProcessed_AutofitCloud-shadi_20191202.pkl"
    fix_fn = os.path.join(BASEDIR, fix_fn)
    #df_post.to_pickle(fix_fn)
    df_exp = pd.read_pickle(fix_fn)

    pd.testing.assert_frame_equal(df_exp, df_post)
