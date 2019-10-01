import logging
logger = logging.getLogger('isitfit')

from .tagsSuggestBasic import TagsSuggestBasic
import os

BUCKET_NAME='isitfit-cli'

class TagsSuggestAdvanced(TagsSuggestBasic):

  def __init__(self):
    # boto3 ec2 and cloudwatch data
    import boto3
    self.sts = boto3.client('sts')
    self.sqs_res = boto3.resource('sqs', region_name='us-east-1') # region matches with the serverless.yml region
    self.s3_client  = boto3.client('s3' )
    return super().__init__()


  def prepare(self):
    logger.info("Advanced suggestion of tags")
    r_ping = self._tags_ping()
    if not 'status' in r_ping:
      raise ValueError("Failed to ping the remote: %s"%r_ping)

    # TODO implement later
    logger.info("tags ping complete")
    print(r_ping)
    logger.info("Can use s3: %s"%r_ping['s3_arn'])
    logger.info("Can use sqs: %s"%r_ping['sqs_url'])
    self.r_ping = r_ping

    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Queue.receive_messages
    self.sqs_q = self.sqs_res.Queue(self.r_ping['sqs_url'])



  def suggest(self):
    import tempfile

    logger.info("Uploading ec2 names to s3")
    with tempfile.NamedTemporaryFile(suffix='csv', prefix='isitfit-ec2names-', delete=True) as fh:
      self.tags_df.to_csv(fh.name, index=False)
      s3_path = os.path.join(self.r_ping['s3_arn'], 'tags_request.csv')
      self.s3_client.put_object(Bucket=BUCKET_NAME, Key=s3_path, Body=fh.name)
      self.sqs_q.send_message(MessageBody='ec2names uploaded')

    # now listen on sqs
    # https://github.com/jegesh/python-sqs-listener/blob/master/sqs_listener/__init__.py#L123
    logger.info("Waiting for results on SQS")
    MAX_RETRIES = 5
    i_retry = 0
    import time
    while i_retry < MAX_RETRIES:
      i_retry += 1

      n_secs = 5
      #logger.info("Sleep %i seconds"%n_secs)
      time.sleep(n_secs)

      logger.info("Check sqs messages (Retry %i/%i)"%(i_retry, MAX_RETRIES))
      messages = self.sqs_q.receive_messages(
        QueueUrl=self.sqs_q.url,
        MaxNumberOfMessages=10
      )
      if 'Messages' in messages:
        logger.info("{} messages received".format(len(messages['Messages'])))
        for m in messages['Messages']:
          if m['Body'] == 'tags processed':
            with tempfile.NamedTemporaryFilename(suffix='csv', prefix='isitfit-tags-suggestAdvanced-', delete=False) as fh:
              s3_path = os.path.join(self.r_ping['s3_arn'], 'tags_suggested.csv')
              response = self.s3_client.get_object(Bucket=BUCKET_NAME, Key=s3_path)
              fh.write(response['Body'].read())
              self.suggested_df = pd.read_csv(fh.name, nrows=MAX_ROWS)
              # count number of rows in csv
              # https://stackoverflow.com/a/36973958/4126114
              with open(fh.name) as f2:
                  self.suggested_shape = [sum(1 for line in f2), 4] # 4 is just hardcoded number of columns that doesn't matter much
              return

    # if nothing returned on sqs
    logger.error("Absolute radio silence on sqs :(")
    import pandas as pd
    self.suggested_df = pd.DataFrame()
    self.suggested_shape = [0,4]
    self.csv_fn = None


  def _tags_ping(self):
      import requests
      # URL = 'https://klrek4vqid.execute-api.us-east-1.amazonaws.com/dev/tags/ping'
      URL = 'https://klrek4vqid.execute-api.us-east-1.amazonaws.com/dev/register'
      import boto3
      sts = boto3.client('sts')
      r_sts = sts.get_caller_identity()
      del r_sts['ResponseMetadata']
      # eg {'UserId': 'AIDA6F3WEM7AXY6Y4VWDC', 'Account': '974668457921', 'Arn': 'arn:aws:iam::974668457921:user/shadi'}

      r_ping = requests.request('post', URL, json=r_sts)
      # https://stackoverflow.com/questions/18810777/how-do-i-read-a-response-from-python-requests
      import json
      r2 = json.loads(r_ping.text)
      return r2
