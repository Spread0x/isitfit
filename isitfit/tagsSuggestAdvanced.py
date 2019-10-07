import logging
logger = logging.getLogger('isitfit')

from .tagsSuggestBasic import TagsSuggestBasic
from .utils import MAX_ROWS
import os
import requests
import json
from .utils import IsitfitError

BASE_URL = 'https://r0ju8gtgtk.execute-api.us-east-1.amazonaws.com'

class TagsSuggestAdvanced(TagsSuggestBasic):

  def __init__(self):
    logger.debug("TagsSuggestAdvanced::constructor")

    # boto3 ec2 and cloudwatch data
    import boto3
    self.sts = boto3.client('sts')
    self.sqs_res = boto3.resource('sqs', region_name='us-east-1') # region matches with the serverless.yml region
    self.s3_client  = boto3.client('s3' )
    return super().__init__()


  def prepare(self):
    logger.debug("TagsSuggestAdvanced::prepare")

    self._register()
    if not 'status' in self.r_register:
      raise IsitfitError("Failed to ping the remote: %s"%self.r_register)

    # TODO implement later
    # print(self.r_register)
    logger.debug("Granted access to s3 arn: %s"%self.r_register['s3_arn'])
    logger.debug("Granted access to sqs url: %s"%self.r_register['sqs_url'])
    logger.debug("Note that account number 974668457921 is AutofitCloud, the company behind isitfit.")
    logger.debug("For more info, visit https://autofitcloud.com/privacy")

    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Queue.receive_messages
    self.sqs_q = self.sqs_res.Queue(self.r_register['sqs_url'])


  def suggest(self):
    logger.debug("TagsSuggestAdvanced::suggest")

    import tempfile

    logger.info("Uploading ec2 names to s3")
    with tempfile.NamedTemporaryFile(suffix='.csv', prefix='isitfit-ec2names-', delete=True) as fh:
      logger.debug("Will use temporary file %s"%fh.name)
      self.tags_df.to_csv(fh.name, index=False)
      self.s3_key_suffix = 'tags_request.csv'
      s3_path = os.path.join(self.r_sts['Account'], self.r_sts['UserId'], self.s3_key_suffix)
      self.s3_client.put_object(Bucket=self.r_register['s3_bucketName'], Key=s3_path, Body=fh)

    # mark timestamp of request
    import datetime as dt
    dt_now = dt.datetime.utcnow() #.strftime('%s')

    # POST /tags/suggest
    self._tags_suggest()

    # now listen on sqs
    # https://github.com/jegesh/python-sqs-listener/blob/master/sqs_listener/__init__.py#L123
    logger.info("Waiting for results")
    MAX_RETRIES = 5
    i_retry = 0
    any_found = False
    import time
    n_secs = 5
    while i_retry < MAX_RETRIES:
      i_retry += 1

      if i_retry == 1:
        time.sleep(1)
      else:
        #logger.info("Sleep %i seconds"%n_secs)
        time.sleep(n_secs)

      logger.debug("Check sqs messages (Retry %i/%i)"%(i_retry, MAX_RETRIES))
      messages = self.sqs_q.receive_messages(
        AttributeNames=['SentTimestamp'],
        QueueUrl=self.sqs_q.url,
        MaxNumberOfMessages=10
      )
      logger.debug("{} messages received".format(len(messages)))
      import datetime as dt
      for m in messages:
          any_found = True
          sentTime_dt = None
          sentTime_str = "-"
          if m.attributes is not None:
            sentTime_dt = m.attributes['SentTimestamp']
            sentTime_dt = dt.datetime.utcfromtimestamp(int(sentTime_dt)/1000)
            sentTime_str = sentTime_dt.strftime("%Y/%m/%d %H:%M:%S")

          logger.debug("Message: %s: %s"%(sentTime_str, m.body))

          try:
            m.body_decoded = json.loads(m.body)
          except json.decoder.JSONDecodeError as e:
            logger.debug("(Invalid message with non-json body. Skipping)")
            continue

          if 'type' not in m.body_decoded:
            # print("FOOOOOOOOOO")
            logger.debug("(Message body missing key 'type'. Skipping)")
            continue

          if m.body_decoded['type'] != 'tags suggest':
            logger.debug("(Message topic = %s != tags suggest. Skipping)")
            continue

          if (sentTime_dt < dt_now):
              logger.debug("(Stale message. Dropping and skipping)")
              m.delete()
              continue

          # all "tags suggest" messages are removed from the queue
          logger.debug("(Message is ok. Will process. Removing from queue)")
          m.delete()

          # process messages
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
              s3_path = os.path.join(self.r_register['s3_keyPrefix'], m.body_decoded['s3_key_suffix'])
              logger.info("Downloading tag suggestions from isitfit server")
              logger.debug("Getting s3 file %s"%s3_path)
              logger.debug("Saving it into %s"%fh.name)
              response = self.s3_client.get_object(Bucket=self.r_register['s3_bucketName'], Key=s3_path)
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


  def _register(self):
      logger.info("Requesting access to isitfit server S3 and SQS")
      logger.debug("POST /register")
      URL = '%s/dev/register'%BASE_URL
      self.r_sts = self.sts.get_caller_identity()
      del self.r_sts['ResponseMetadata']
      # eg {'UserId': 'AIDA6F3WEM7AXY6Y4VWDC', 'Account': '974668457921', 'Arn': 'arn:aws:iam::974668457921:user/shadi'}

      r1 = requests.request('post', URL, json=self.r_sts)

      # https://stackoverflow.com/questions/18810777/how-do-i-read-a-response-from-python-requests
      self.r_register = json.loads(r1.text)

      # check for internal server error
      if 'message' in self.r_register:
        if self.r_register['message']=='Internal server error':
          raise IsitfitError('Internal server error')

      # check schema
      from schema import Schema, Optional, SchemaError
      register_schema = Schema({
        'status': str,
        's3_arn': str,
        's3_bucketName': str,
        's3_keyPrefix': str,
        'sqs_url': str,
        Optional(str): object
      })
      try:
        register_schema.validate(self.r_register)
      except SchemaError as e:
        logger.error("Received response: %s"%r1.text)
        raise IsitfitError("Invalid register response: %s"%str(e))



  def _tags_suggest(self):
      logger.info("Requesting tag suggestions from isitfit server")
      logger.debug("POST /tags/suggest")
      URL = '%s/dev/tags/suggest'%BASE_URL
      load_send = {}
      load_send.update(self.r_sts)
      load_send['s3_key_suffix'] = self.s3_key_suffix
      load_send['sqs_url'] = self.r_register['sqs_url']
      r_tagsSuggest = requests.request('post', URL, json=load_send)
      # https://stackoverflow.com/questions/18810777/how-do-i-read-a-response-from-python-requests
      r2 = json.loads(r_tagsSuggest.text)

      if 'error' in r2:
        print(r2)
        raise IsitfitError('Serverside error: %s'%r2['error'])

      if 'message' in r2:
        print(r2)
        raise IsitfitError('Serverside error: %s'%r2['message'])

      return r2
