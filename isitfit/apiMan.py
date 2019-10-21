import logging
logger = logging.getLogger('isitfit')

# URL of isitfit API
#BASE_URL = 'https://r0ju8gtgtk.execute-api.us-east-1.amazonaws.com/dev/'
BASE_URL = 'https://api.isitfit.io/v0/'


from aws_requests_auth.boto_utils import BotoAWSRequestsAuth
class MyBotoAWSRequestsAuth(BotoAWSRequestsAuth):
    def __init__(self, boto_session=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # over-write the credentials until a PR is made to integrate this upstream
        # https://github.com/DavidMuller/aws-requests-auth/blob/master/aws_requests_auth/boto_utils.py
        if boto_session is None: boto_session = boto3.session.Session()
        self._refreshable_credentials = boto_session.get_credentials()


class ApiMan:

  # counter of number of "register" calls
  call_n = 0 
  
  # class member holding register response
  r_register = None

  def __init__(self, tryAgainIn):
      self.tryAgainIn = tryAgainIn

  def register(self):
      logger.debug("ApiMan::register")

      if self.r_register is not None:
          if self.r_register['status']=='ok':
              # already registered
              return

      # counter
      self.call_n += 1

      # display head
      if self.call_n == 1:
          logger.info("Logging into server")
      else:
          logger.info("Registration attempt # %i."%(self.call_n))


      import boto3
      sts_client = boto3.client('sts')
      self.r_sts = sts_client.get_caller_identity()
      del self.r_sts['ResponseMetadata']
      # eg {'UserId': 'AIDA6F3WEM7AXY6Y4VWDC', 'Account': '974668457921', 'Arn': 'arn:aws:iam::974668457921:user/shadi'}

      # actual request
      self.r_register, dt_now = self.request(
        method='post',
        relative_url='./register',
        payload_json=self.r_sts,
        authenticated_user_path=False # since /register is the absolute path (without account/user)
      )

      # deal with "registration in progrss"
      if 'error' in self.r_register:
        raise IsitfitError("Failed to log in: %s"%self.r_register)
  
      if 'status' not in self.r_register:
        raise IsitfitError("Failed to log in: %s"%self.r_register)
  
      if self.r_register['status']=='Registration in progress':
          # status
          if self.call_n==1:
              # just continue and will check again later
              logger.info("Registration in progress")
          elif self.call_n==2:
              logger.info("Registration not ready yet.")
          else:
              raise IsitfitError("Registration is still not ready. Please try again in a few minutes, or file an issue at https://github.com/autofitcloud/isitfit/issues")

          if self.call_n >= self.tryAgainIn:
              nsecs_wait = 30
              logger.info("Will check again in %i seconds"%(nsecs_wait))
              import time
              time.sleep(nsecs_wait)
              self.register()
              return


      if self.r_register['status']!='ok':
          raise IsitfitError("Failed to log in: unknown status returned: %s"%self.r_register)

      # at this stage, registration was ok, so proceed
      if self.call_n==1:
          logger.info("Registration already done earlier")
      else:
          logger.info("Registration complete")

      # show resources granted
      # print(self.r_register)
      logger.debug("Granted access to s3 arn: %s"%self.r_register['s3_arn'])
      logger.debug("Granted access to sqs url: %s"%self.r_register['sqs_url'])
      logger.debug("Note that account number 974668457921 is AutofitCloud, the company behind isitfit.")
      logger.debug("For more info, visit https://autofitcloud.com/privacy")

      # check schema
      from schema import SchemaError, Schema, Optional
      register_schema = Schema({
        'status': str,
        's3_arn': str,
        's3_bucketName': str,
        's3_keyPrefix': str,
        'sqs_url': str,
        'role_arn': str,
        Optional(str): object
      })

      try:
        register_schema.validate(self.r_register)
      except SchemaError as e:
        logger.error("Received response: %s"%self.r_register.text)
        raise IsitfitError("Does not match expected schema: %s"%str(e))

      # get boto3 session using the assumed role
      # for further use of aws resources from AutofitCloud
      # eg API Gateway, S3, SQS
      sts_connection = boto3.client('sts')
      acct_b = sts_connection.assume_role(
                RoleArn=self.r_register['role_arn'],
                #ExternalId=None, # TODO set external ID?
                RoleSessionName="cross_acct_isitfit"
      )
      self.boto3_session =  boto3.session.Session(
        aws_access_key_id=acct_b['Credentials']['AccessKeyId'],
        aws_secret_access_key=acct_b['Credentials']['SecretAccessKey'],
        aws_session_token=acct_b['Credentials']['SessionToken'],
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Queue.receive_messages
        # region matches with the serverless.yml region
        region_name='us-east-1'
      )

      # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Queue.receive_messages
      # region matches with the serverless.yml region
      sqs_res = self.boto3_session.resource('sqs') # no need for region since already in boto session # , region_name='us-east-1')
      self.sqs_q = sqs_res.Queue(self.r_register['sqs_url'])


  def request(self, method, relative_url, payload_json, authenticated_user_path=True):
      """
      Wrapper to the URL request
      method - post
      relative_url - eg ./tags/suggest
      payload_json - "json" field for request call
      authenticated_user_path - flag for self.register which can disable this as it doesn't have a account/user prefix in the URL
      """
      logger.debug("ApiMan::request")

      # relative URL to absolute
      # https://stackoverflow.com/a/8223955/4126114
      if authenticated_user_path:
        suffix_url='./%s/%s/%s'%(self.r_sts['Account'], self.r_sts['UserId'], relative_url)
      else:
        suffix_url = relative_url

      import urllib.parse
      absolute_url = urllib.parse.urljoin(BASE_URL, suffix_url)
      import json
      logger.debug("%s %s %s"%(method, absolute_url, json.dumps(payload_json)))

      # prepare to use AWS Sigv4 with requests
      # https://stackoverflow.com/a/47252241/4126114
      #
      # use boto3 to collect credentials
      # https://github.com/DavidMuller/aws-requests-auth#using-boto-to-automatically-gather-aws-credentials
      #
      # original aws post (not clear)
      # https://docs.aws.amazon.com/general/latest/gr/sigv4-signed-request-examples.html
      #
      # clearer aws post
      # https://aws.amazon.com/premiumsupport/knowledge-center/iam-authentication-api-gateway/
      import boto3
      boto_session=self.boto3_session if authenticated_user_path else boto3.session.Session()

      auth = MyBotoAWSRequestsAuth(aws_host='api.isitfit.io',
                                    aws_region='us-east-1',
                                    aws_service='execute-api',
                                    # sign with the assumed role's credentials
                                    boto_session=boto_session
                                    )

      # mark timestamp right before request (used in listen_sqs for dropping stale messages)
      import datetime as dt
      dt_now = dt.datetime.utcnow() #.strftime('%s')

      # make actual request
      import requests
      r1 = requests.request(method, absolute_url, json=payload_json, auth=auth)
      #logger.debug("python requests http request header:")
      #logger.debug(r1.request.headers)

      # https://stackoverflow.com/questions/18810777/how-do-i-read-a-response-from-python-requests
      import json
      r2 = json.loads(r1.text)

      # check for errors
      from .utils import IsitfitError
      if 'error' in r2:
        # print(r2)
        raise IsitfitError('Serverside error #1: %s'%r2['error'])

      if 'message' in r2:
        if r2['message']=='Internal server error':
          raise IsitfitError('Internal server error')
        else:
          # print(r2)
          raise IsitfitError('Serverside error #2: %s'%r2['message'])

      # if no schema provided
      return r2, dt_now


  def listen_sqs(self, expected_type, dt_now):
    """
    expected_type - value of field "type" in the SQS messages to target
    dt_now - timestamp right before issuing the http that could have triggered the SQS messages
             Used to drop "stale" messages from earlier/canceled runs
    """
    # now listen on sqs

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
      import json
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
              logger.debug("Stale message (msg = %s < now = %s). Dropping and skipping"%(sentTime_dt, dt_now))
              m.delete()
              continue

          # all "tags suggest" messages are removed from the queue
          logger.debug("(Message is ok. Will process. Removing from queue)")
          m.delete()

          # process messages
          yield m

    # done
    yield None
