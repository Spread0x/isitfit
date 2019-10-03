import logging
logger = logging.getLogger('isitfit')

from .tagsSuggestBasic import TagsSuggestBasic
import os
import requests
import json

BUCKET_NAME='isitfit-cli'
BASE_URL = 'https://r0ju8gtgtk.execute-api.us-east-1.amazonaws.com'

class TagsSuggestAdvanced(TagsSuggestBasic):

  def __init__(self):
    # boto3 ec2 and cloudwatch data
    import boto3
    self.sts = boto3.client('sts')
    self.sqs_res = boto3.resource('sqs', region_name='us-east-1') # region matches with the serverless.yml region
    self.s3_client  = boto3.client('s3' )
    return super().__init__()


  def prepare(self):
    self.r_register = self._register()
    if not 'status' in self.r_register:
      raise ValueError("Failed to ping the remote: %s"%self.r_register)

    # TODO implement later
    # print(self.r_register)
    logger.info("Will use s3 arn: %s"%self.r_register['s3_arn'])
    logger.info("Will use sqs url: %s"%self.r_register['sqs_url'])

    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Queue.receive_messages
    self.sqs_q = self.sqs_res.Queue(self.r_register['sqs_url'])


  def suggest(self):
    import tempfile

    logger.info("Uploading ec2 names to s3")
    with tempfile.NamedTemporaryFile(suffix='csv', prefix='isitfit-ec2names-', delete=True) as fh:
      self.tags_df.to_csv(fh.name, index=False)
      self.s3_key_suffix = 'tags_request.csv'
      s3_path = os.path.join(self.r_sts['Account'], self.r_sts['UserId'], self.s3_key_suffix)
      self.s3_client.put_object(Bucket=BUCKET_NAME, Key=s3_path, Body=fh.name)

    # POST /tags/suggest
    self._tags_suggest()

    # now listen on sqs
    # https://github.com/jegesh/python-sqs-listener/blob/master/sqs_listener/__init__.py#L123
    logger.info("Waiting for results on SQS")
    MAX_RETRIES = 5
    i_retry = 0
    any_found = False
    import time
    while i_retry < MAX_RETRIES:
      i_retry += 1

      n_secs = 5
      #logger.info("Sleep %i seconds"%n_secs)
      time.sleep(n_secs)

      logger.info("Check sqs messages (Retry %i/%i)"%(i_retry, MAX_RETRIES))
      messages = self.sqs_q.receive_messages(
        AttributeNames=['SentTimestamp'],
        QueueUrl=self.sqs_q.url,
        MaxNumberOfMessages=10
      )
      logger.info("{} messages received".format(len(messages)))
      import datetime as dt
      for m in messages:
          any_found = True
          sentTime = "-"
          if m.attributes is not None:
            sentTime = m.attributes['SentTimestamp']
            sentTime = dt.datetime.utcfromtimestamp(int(sentTime)/1000).strftime("%Y/%m/%d %H:%M:%S")

          logger.info("Message: %s: %s"%(sentTime, m.body))
          m.delete()
          if m.body == 'tags processed':
            with tempfile.NamedTemporaryFilename(suffix='csv', prefix='isitfit-tags-suggestAdvanced-', delete=False) as fh:
              s3_path = os.path.join(self.r_register['s3_arn'], 'tags_suggested.csv')
              response = self.s3_client.get_object(Bucket=BUCKET_NAME, Key=s3_path)
              fh.write(response['Body'].read())
              self.suggested_df = pd.read_csv(fh.name, nrows=MAX_ROWS)
              # count number of rows in csv
              # https://stackoverflow.com/a/36973958/4126114
              with open(fh.name) as f2:
                  self.suggested_shape = [sum(1 for line in f2), 4] # 4 is just hardcoded number of columns that doesn't matter much
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
      logger.info("POST /register")
      URL = '%s/dev/register'%BASE_URL
      self.r_sts = self.sts.get_caller_identity()
      del self.r_sts['ResponseMetadata']
      # eg {'UserId': 'AIDA6F3WEM7AXY6Y4VWDC', 'Account': '974668457921', 'Arn': 'arn:aws:iam::974668457921:user/shadi'}

      r_register = requests.request('post', URL, json=self.r_sts)
      # https://stackoverflow.com/questions/18810777/how-do-i-read-a-response-from-python-requests
      r2 = json.loads(r_register.text)
      return r2


  def _tags_suggest(self):
      logger.info("POST /tags/suggest")
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
        raise ValueError('Serverside error: %s'%r2['error'])

      if 'message' in r2:
        print(r2)
        raise ValueError('Serverside error: %s'%r2['message'])

      return r2
