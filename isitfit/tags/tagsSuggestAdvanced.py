import logging
logger = logging.getLogger('isitfit')

from .tagsSuggestBasic import TagsSuggestBasic
from ..utils import MAX_ROWS, IsitfitError
import os
import json
from ..apiMan import ApiMan

class TagsSuggestAdvanced(TagsSuggestBasic):

  def __init__(self):
    logger.debug("TagsSuggestAdvanced::constructor")

    # boto3 ec2 and cloudwatch data
    import boto3
    self.s3_client  = boto3.client('s3' )

    # api manager
    self.api_man = ApiMan()

    # proceed with parent constructor
    return super().__init__()


  def prepare(self):
    logger.debug("TagsSuggestAdvanced::prepare")

    self.api_man.register()

    if not 'status' in self.api_man.r_register:
      raise IsitfitError("Failed to ping the remote: %s"%self.api_man.r_register)

    # TODO implement later
    # print(self.api_man.r_register)
    logger.debug("Granted access to s3 arn: %s"%self.api_man.r_register['s3_arn'])
    logger.debug("Granted access to sqs url: %s"%self.api_man.r_register['sqs_url'])
    logger.debug("Note that account number 974668457921 is AutofitCloud, the company behind isitfit.")
    logger.debug("For more info, visit https://autofitcloud.com/privacy")


  def suggest(self):
    logger.debug("TagsSuggestAdvanced::suggest")

    import tempfile

    logger.info("Uploading ec2 names to s3")
    with tempfile.NamedTemporaryFile(suffix='.csv', prefix='isitfit-ec2names-', delete=True) as fh:
      logger.debug("Will use temporary file %s"%fh.name)
      self.tags_df.to_csv(fh.name, index=False)
      self.s3_key_suffix = 'tags_request.csv'
      s3_path = os.path.join(self.api_man.r_sts['Account'], self.api_man.r_sts['UserId'], self.s3_key_suffix)
      self.s3_client.put_object(Bucket=self.api_man.r_register['s3_bucketName'], Key=s3_path, Body=fh)

    # POST /tags/suggest
    self._tags_suggest()

    # now listen on sqs
    any_found = False
    for m in self.api_man.listen_sqs('tags suggest'):
      # if done
      if m is None: break

      # process messages
      any_found = True
      logger.info("Server message: %s"%m.body_decoded['status'])
      if m.body_decoded['status'] != 'calculation complete':
        continue

      if m.body_decoded['status'] == 'calculation complete':
        # upon calculation complete message
        if 's3_key_suffix' not in m.body_decoded:
          logger.debug("(Missing s3_key_suffix key from body. Aborting)")
          return

        self.csv_fn = None
        with tempfile.NamedTemporaryFile(suffix='.csv', prefix='isitfit-tags-suggestAdvanced-', delete=False) as fh:
          self.csv_fn = fh.name
          s3_path = os.path.join(self.api_man.r_register['s3_keyPrefix'], m.body_decoded['s3_key_suffix'])
          logger.info("Downloading tag suggestions from isitfit server")
          logger.debug("Getting s3 file %s"%s3_path)
          logger.debug("Saving it into %s"%fh.name)
          response = self.s3_client.get_object(Bucket=self.api_man.r_register['s3_bucketName'], Key=s3_path)
          fh.write(response['Body'].read())

        logger.debug("TagsSuggestAdvanced:suggest .. read_csv")
        import pandas as pd
        self.suggested_df = pd.read_csv(self.csv_fn, nrows=MAX_ROWS)

        # count number of rows in csv
        # https://stackoverflow.com/a/36973958/4126114
        logger.debug("TagsSuggestAdvanced:suggest .. count_rows")
        with open(fh.name) as f2:
            self.suggested_shape = [sum(1 for line in f2), 4] # 4 is just hardcoded number of columns that doesn't matter much

        logger.debug("TagsSuggestAdvanced:suggest .. done")
        return

    # if nothing returned on sqs
    if not any_found:
      logger.error("Absolute radio silence on sqs :(")

    # either no sqs messages,
    # or found some sqs messages, but none were for tags request fulfilled
    import pandas as pd
    self.suggested_df = pd.DataFrame()
    self.suggested_shape = [0,4]
    self.csv_fn = None


  def _tags_suggest(self):
      logger.info("Requesting tag suggestions from isitfit server")

      load_send = {}
      load_send.update(self.api_man.r_sts)
      load_send['s3_key_suffix'] = self.s3_key_suffix
      load_send['sqs_url'] = self.api_man.r_register['sqs_url']

      r2 = self.api_man.request(
        method='post',
        relative_url='./tags/suggest',
        payload_json=load_send,
        response_schema=None
      )

      return r2
