import logging
logger = logging.getLogger('isitfit')

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
    import redis
    import pyarrow as pa

    self.redis_client = redis.Redis(**self.redis_args)
    self.pyarrow_context = pa.default_serialization_context()

  def isReady(self):
    return self.redis_client is not None

  def set(self, key, df):
    # Note that in case data was not found, eg in mainManager._cloudwatch_metrics_core, an empty dataframe is returned (and thus passed in here)
    pybytes = self.pyarrow_context.serialize(df).to_buffer().to_pybytes()
    # set expiration of key-value pair to be 1 day if data was found, 10 minutes otherwise
    ex = SECONDS_IN_10MINS if df.shape[0]==0 else SECONDS_IN_ONE_DAY
    # https://redis-py.readthedocs.io/en/latest/#redis.Redis.set
    self.redis_client.set(name=key, value=pybytes, ex=ex)

  def get(self, key):
    v1 = self.redis_client.get(key)
    if not v1: return v1
    v2 = self.pyarrow_context.deserialize(v1)
    return v2
