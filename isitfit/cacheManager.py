import logging
logger = logging.getLogger('isitfit')

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
    return any(self.redis_args.values())

  def connect(self):
    logger.info("Connecting to redis cache")
    import redis
    import pyarrow as pa

    self.redis_client = redis.Redis(**self.redis_args)
    self.pyarrow_context = pa.default_serialization_context()

  def isReady(self):
    return self.redis_client is not None

  def set(self, key, df):
    pybytes = self.pyarrow_context.serialize(df).to_buffer().to_pybytes()
    self.redis_client.set(key, pybytes)

  def get(self, key):
    v1 = self.redis_client.get(key)
    if not v1: return v1
    v2 = self.pyarrow_context.deserialize(v1)
    return v2
