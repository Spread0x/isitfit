import logging
logger = logging.getLogger('isitfit')

# URL of isitfit API
#BASE_URL = 'https://r0ju8gtgtk.execute-api.us-east-1.amazonaws.com/dev/'
BASE_URL = 'https://api.isitfit.io/v0/'

class ApiMan:

  def register(self):
      logger.debug("ApiMan::register")
      logger.info("Logging into server")

      import boto3
      sts_client = boto3.client('sts')
      self.r_sts = sts_client.get_caller_identity()
      del self.r_sts['ResponseMetadata']
      # eg {'UserId': 'AIDA6F3WEM7AXY6Y4VWDC', 'Account': '974668457921', 'Arn': 'arn:aws:iam::974668457921:user/shadi'}

      # check schema
      from schema import Schema, Optional
      register_schema = Schema({
        'status': str,
        's3_arn': str,
        's3_bucketName': str,
        's3_keyPrefix': str,
        'sqs_url': str,
        Optional(str): object
      })

      # actual request
      self.r_register = self.request(
        method='post',
        relative_url='./register',
        json=self.r_sts,
        response_schema=register_schema
      )

      # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Queue.receive_messages
      self.sqs_q = self.sqs_res.Queue(self.r_register['sqs_url'])


  def request(self, method, relative_url, payload_json, response_schema):
      """
      Wrapper to the URL request
      method - post
      relative_url - eg ./tags/suggest
      payload_json - "json" field for request call
      response_schema - optional schema to validate response
      """
      logger.debug("ApiMan::request")

      logger.info("Sending data to API")
      logger.debug("%s %s"%(method, relative_url))

      # relative URL to absolute
      # https://stackoverflow.com/a/8223955/4126114
      import urllib.parse
      absolute_url = urllib.parse.urljoin(BASE_URL, relative_url)

      # make actual request
      import requests
      r1 = requests.request(method, absolute_url, payload_json=payload_json)

      # https://stackoverflow.com/questions/18810777/how-do-i-read-a-response-from-python-requests
      import json
      r2 = json.loads(r1.text)

      # check for errors
      from ..utils import IsitfitError
      if 'error' in r2:
        print(r2)
        raise IsitfitError('Serverside error: %s'%r2['error'])

      if 'message' in r2:
        if self.r_register['message']=='Internal server error':
          raise IsitfitError('Internal server error')
        else:
          print(r2)
          raise IsitfitError('Serverside error: %s'%r2['message'])

      # every http transaction requires a SQS authenticated handshake
      # self._handshake_sqs()

      # if no schema provided
      if response_schema is None:
        return r2

      # check schema
      from schema import SchemaError
      try:
        response_schema.validate(r2)
      except SchemaError as e:
        logger.error("Received response: %s"%r1.text)
        raise IsitfitError("Does not match expected schema: %s"%str(e))


      # if all ok
      return r2


#  def _handshake_sqs(self):
#    # listen
#    for m in self.listen_sqs('handshake'):
#      if m is not None:
#        # respond with handshake
#        self.sqs_q.send_message(MessageBody='handshake')
#
#      # exactly 1 message
#      break
#
#    # if no handshake
#    raise IsitfitError("No handshake received")


  def listen_sqs(self, expected_type):
    # now listen on sqs

    # mark timestamp of request
    import datetime as dt
    dt_now = dt.datetime.utcnow() #.strftime('%s')

    # https://github.com/jegesh/python-sqs-listener/blob/master/sqs_listener/__init__.py#L123
    logger.info("Waiting for results")
    MAX_RETRIES = 5
    i_retry = 0
    import time
    n_secs = 5

    # loop
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

          if m.body_decoded['type'] != expected_type:
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
          yield m

    # done
    yield None
