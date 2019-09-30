import logging
logger = logging.getLogger('isitfit')

from .tagsSuggestBasic import TagsSuggestBasic


class TagsSuggestAdvanced(TagsSuggestBasic):

  def __init__(self):
    # boto3 ec2 and cloudwatch data
    import boto3
    self.sts = boto3.client('sts')
    self.sqs_client = boto3.client('sqs')
    self.s3  = boto3.client('s3' )
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
    logger.info("Can use sqs: %s"%r_ping['sqs_arn'])
    self.r_ping = r_ping

    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Queue.receive_messages
    self.sqs_q = self.sqs_client.Queue(self.r_ping['sqs_arn'])



  def suggest(self, names_df):
    s3 = boto3.resource('s3')
    with tempfile.NamedTemporaryFilename(suffix='csv', prefix='isitfit-ec2names-', delete=True) as fh:
      tags_df.to_csv(fh.name, index=False)
      s3_path = os.path.join(self.r_ping['s3_arn'], 'tags_request.csv')
      self.s3.upload(fh.name, self.r_ping['s3_arn'])
      self.sqs_q.send_message(MessageBody='ec2names uploaded')

    # now listen on sqs
    # https://github.com/jegesh/python-sqs-listener/blob/master/sqs_listener/__init__.py#L123
    messages = self.sqs_q.receive_message(
        QueueUrl=self.sqs_q.url,
        MaxNumberOfMessages=10
    )
    if 'Messages' in messages:
        logger.info("{} messages received".format(len(messages['Messages'])))
        for m in messages['Messages']:
          if m['Body'] == 'tags processed':
            with tempfile.NamedTemporaryFilename(suffix='csv', prefix='isitfit-tags-suggestAdvanced-', delete=False) as fh:
              s3_path = os.path.join(self.r_ping['s3_arn'], 'tags_suggested.csv')
              s3.cp(s3_path, fh.name)
              suggested_df = pd.read_csv(fh.name, nrows=MAX_ROWS)
              logger.info("")
              logger.info("Suggested tags:")
              logger.info(suggested_df)
              logger.info("...")
              logger.info(colored("Dumping data into %s"%fh.name, "cyan"))
              return


  def _tags_ping(self):
      import requests
      URL = 'https://w7qqwtfzp4.execute-api.us-east-1.amazonaws.com/dev/tags/ping'
      import boto3
      sts = boto3.client('sts')
      r_sts = sts.get_caller_identity()
      r_ping = requests.request('post', URL, data=r_sts)
      # https://stackoverflow.com/questions/18810777/how-do-i-read-a-response-from-python-requests
      import json
      r2 = json.loads(r_ping.text)
      return r2
