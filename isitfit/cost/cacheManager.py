from isitfit.utils import logger
import pandas as pd
import redis


from ..utils import SECONDS_IN_ONE_DAY
SECONDS_IN_10MINS = 60*10

class RedisPandas:
  """
  Python class that manages caching pandas dataframes to redis
  https://stackoverflow.com/a/57986261/4126114
  """
  def __init__(self):
    self.redis_args = {}
    self.redis_client = None
    self.pyarrow_context = None

  def fetch_envvars(self):
    # check redis parameters if set for caching
    import os
    for k1, k2 in [
        ('host', "ISITFIT_REDIS_HOST"),
        ('port', "ISITFIT_REDIS_PORT"),
        ('db', "ISITFIT_REDIS_DB")
      ]:
      self.redis_args[k1] = os.getenv(k2, None)

  def isSetup(self):
    return all(self.redis_args.values())

  def connect(self):
    logger.info("Connecting to redis cache")
    logger.debug(self.redis_args)
    import pyarrow as pa

    self.redis_client = redis.Redis(**self.redis_args)
    self.pyarrow_context = pa.default_serialization_context()

  def isReady(self):
    return self.redis_client is not None

  def set(self, key, df):
    # Note that in case data was not found, eg in mainManager._cloudwatch_metrics_core, an empty dataframe is returned (and thus passed in here)
    pybytes = self.pyarrow_context.serialize(df).to_buffer().to_pybytes()

    # if dataframe with shape[0]==0, raise (no longer supported)
    # Update 2019-12-17 Actually Cloudtrail needs to store an empty dataframe if there are no events in the last 90 days
    if not callable(df):
      from isitfit.cli.click_descendents import IsitfitCliError

      if type(df) != pd.DataFrame:
        raise IsitfitCliError("Internal dev error: Only caching of callables or pandas dataframes supported as of isitfit 0.19")

      # Check comment above about Cloudtrail needing to store empty dataframes
      #if df.shape[0]==0:
      #  raise IsitfitCliError("Internal dev error: caching empty dataframes is no longer supported as of isitfit 0.19")

    # set expiration of key-value pair to be 1 day if data was found, 10 minutes otherwise
    ex = SECONDS_IN_10MINS if callable(df) else SECONDS_IN_ONE_DAY
    # https://redis-py.readthedocs.io/en/latest/#redis.Redis.set
    self.redis_client.set(name=key, value=pybytes, ex=ex)

  def get(self, key):
    try:
      v1 = self.redis_client.get(key)
    except redis.exceptions.ResponseError as e:
      msg = 'Redis error: {e.__class__.__module__}.{e.__class__.__name__}: {e}'.format(e=e)
      # eg, 'redis.exceptions.ResponseError: invalid DB index'
      if 'invalid DB index' in str(e):
        import os
        msg += "\nHint: Check that environment variable ISITFIT_REDIS_DB=%s is a valid redis database index"%(os.getenv("ISITFIT_REDIS_DB", None))
        msg += "\nFor more info: https://stackoverflow.com/questions/13386053/how-do-i-change-between-redis-database"

      from isitfit.cli.click_descendents import IsitfitCliError
      raise IsitfitCliError(msg)

    if not v1: return v1
    v2 = self.pyarrow_context.deserialize(v1)
    return v2

  def handle_pre(self, context_pre):
        # set up caching if requested
        self.fetch_envvars()
        if self.isSetup():
          self.connect()

        # 0th pass to count
        n_ec2_total = context_pre['n_ec2_total']

        # if more than 10 servers, recommend caching with redis
        cond_prompt = n_ec2_total > 10 and not self.isSetup()
        if cond_prompt:
            from termcolor import colored
            logger.warning(colored(
"""Since the number of EC2 instances is %i,
it is recommended to use redis for caching of downloaded CPU/memory metrics.
To do so
- install redis

    [sudo] apt-get install redis-server

- export environment variables

    export ISITFIT_REDIS_HOST=localhost
    export ISITFIT_REDIS_PORT=6379
    export ISITFIT_REDIS_DB=0

where ISITFIT_REDIS_DB is the ID of an unused database in redis.

And finally re-run isitfit as usual.
"""%n_ec2_total, "yellow"))
            import click
            # not using abort=True so that I can send a cusomt message in the abort
            continue_wo_redis = click.confirm(colored('Would you like to continue without redis caching? ', 'cyan'), abort=False, default=True)
            if not continue_wo_redis:
                from isitfit.cli.click_descendents import IsitfitCliError
                raise IsitfitCliError("Aborting to set up redis.", context_pre['click_ctx'])


        # done
        return context_pre


from isitfit.utils import logger, NoCloudwatchException, HostNotFoundInDdg, DataNotFoundForHostInDdg

from isitfit.utils import myreturn
class MetricCacheMixin:
    """
    Mixin for metrics_* classes to get Caching
    """
    def __init__(self, cache_man):
      """
      cache_man - RedisPandasCacheManager
      """
      self.cache_man = cache_man
      super().__init__()


    def get_key(self, host_id):
      raise Exception("Define in derived/mixin")


    def get_metrics_base(self, rc_describe_entry, rc_id, rc_created):
      raise Exception("Define in derived/mixin")


    def get_metrics_derived(self, rc_describe_entry, rc_id, rc_created):
        # check cache first
        cache_key = self.get_key(rc_id)

        if self.cache_man.isReady():
          df_cache = self.cache_man.get(cache_key)
          if df_cache is None:
            # not found
            pass
          else:
            if callable(df_cache):
              # if one of the raise_* functions is cached
              df_cache()

            elif type(df_cache) is pd.DataFrame:
              if df_cache.shape[0]==0:
                # found but no data
                raise Exception("As of isitfit 0.19, empty dataframes are no longer cached")
              else:
                logger.debug("Found metrics (datadog? cloudwatch?)  in redis cache for %s, and data.shape[0] = %i"%(rc_id, df_cache.shape[0]))
                # replace with None if .shape[0]==0
                df_cache = myreturn(df_cache)
                # done
                return df_cache
            else:
              raise ValueError("Invalid value in cache for %s"%cache_key)

        # if no cache, then download
        df_fresh = pd.DataFrame() # use an empty dataframe in order to distinguish when getting from cache if not available in cache or data not found but set in cache
        def error2func(error):
          def raiseme(): raise error
          return raiseme

        try:
          df_fresh = self.get_metrics_base(rc_describe_entry, rc_id, rc_created)
        except HostNotFoundInDdg as error:
          df_fresh = error2func(error)
        except DataNotFoundForHostInDdg as error:
          df_fresh = error2func(error)
        except NoCloudwatchException as error:
          df_fresh = error2func(error)
        except:
          # anything else should bubble up
          raise

        # if caching enabled, store it for later fetching
        # https://stackoverflow.com/a/57986261/4126114
        # Note that this even stores the result if it was "None" (meaning that no data was found)
        if self.cache_man.isReady():
          self.cache_man.set(cache_key, df_fresh)

        # if exception
        if callable(df_fresh):
          df_fresh()

        # done
        return myreturn(df_fresh)

