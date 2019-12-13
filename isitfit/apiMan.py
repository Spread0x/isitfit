from isitfit.utils import logger


# URL of isitfit API
BASE_HOST = 'api.isitfit.io' # FIXME this should be in master
# BASE_HOST = 'api-dev.isitfit.io' # FIXME do not push this into master
BASE_PREFIX = 'v0'
BASE_URL = 'https://%s/%s/'%(BASE_HOST, BASE_PREFIX)

from isitfit.cli.click_descendents import IsitfitCliError
from schema import SchemaError, Schema, Optional


from aws_requests_auth.boto_utils import BotoAWSRequestsAuth
class MyBotoAWSRequestsAuth(BotoAWSRequestsAuth):
    def __init__(self, boto_session=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # over-write the credentials until a PR is made to integrate this upstream
        # https://github.com/DavidMuller/aws-requests-auth/blob/master/aws_requests_auth/boto_utils.py
        if boto_session is None: boto_session = boto3.session.Session()
        self._refreshable_credentials = boto_session.get_credentials()


class ApiMan:

  # number of seconds to wait between re-calls to register
  nsecs_wait = 30

  # counter of number of "register" calls
  call_n = 0 
  
  # class member holding register response
  r_register = None

  # class member shortcut for r_register['isitfitapi_body']
  r_body = None

  # number of times to call register before failing
  n_maxCalls = 3

  def __init__(self, tryAgainIn, ctx):
      self.tryAgainIn = tryAgainIn
      self.ctx = ctx

  def register(self):
      logger.debug("ApiMan::register")

      if self.r_register is not None:
          if self.r_register['isitfitapi_status']['code']=='ok':
              # already registered
              self.r_body = self.r_register['isitfitapi_body']
              return

      # counter
      self.call_n += 1

      # display head
      if self.call_n == 1:
          logger.debug("Logging into server")
      else:
          logger.debug("Registration attempt # %i."%(self.call_n))


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

      # set shortcut to body only
      self.r_body = self.r_register['isitfitapi_body']

      # handle registration in progress
      if self.r_register['isitfitapi_status']['code']=='Registration in progress':
          # deal with "registration in progress"
          if self.call_n==1:
              # just continue and will check again later
              logger.debug("Registration in progress")
          elif self.call_n >= self.n_maxCalls:
              raise IsitfitCliError("Registration is still not ready. Please try again in a few minutes, or file an issue at https://github.com/autofitcloud/isitfit/issues", self.ctx)
          else:
              logger.debug("Registration not ready yet.")

          if self.call_n >= self.tryAgainIn:
              logger.debug("Will check again in %i seconds"%(self.nsecs_wait))
              import time
              #from tqdm import tqdm as tqdm_obj
              from isitfit.tqdmman import TqdmL2Verbose
              tqdm_obj = TqdmL2Verbose(self.ctx)
              tqdm_iter = tqdm_obj(range(self.nsecs_wait), desc="First-time service access (isitfit.io) takes ~ 1 minute")
              for i in tqdm_iter:
                time.sleep(1)

              self.register()
              return

          # stop here
          return


      # at this stage, registration was ok, so proceed
      if self.call_n==1:
          logger.debug("Registration already done earlier")
      else:
          logger.debug("Registration complete")


      # check schema
      register_schema_1 = Schema({
        's3_arn': str,
        's3_bucketName': str,
        's3_keyPrefix': str,
        'sqs_url': str,
        'role_arn': str,
        Optional(str): object
      })

      try:
        register_schema_1.validate(self.r_body)
      except SchemaError as e:
        import json
        logger.error("Received response: %s"%json.dumps(self.r_body))
        raise IsitfitCliError("Does not match expected schema: %s"%str(e), self.ctx)

      # show resources granted
      # print(self.r_register)
      logger.debug("AutofitCloud granted you access to the following AWS resources:")
      from tabulate import tabulate
      logger.debug(tabulate([(k, self.r_body[k]) for k in self.r_body.keys()]))
      logger.debug("Note that account number 974668457921 is AutofitCloud, the company behind isitfit.")
      logger.debug("For more info, visit https://autofitcloud.com/privacy")

      # get boto3 session using the assumed role
      # for further use of aws resources from AutofitCloud
      # eg API Gateway, S3, SQS
      sts_connection = boto3.client('sts')
      acct_b = sts_connection.assume_role(
                RoleArn=self.r_body['role_arn'],

                # TODO set external ID?
                #ExternalId=None,

                # this is a generic session name that shows up in the User ID field
                # on the server-side. If this gets modified, make sure to modify the
                # counter-part in isitfit-api
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
      self.sqs_q = sqs_res.Queue(self.r_body['sqs_url'])


  def _get_auth(self, authenticated_user_path, anonymous_user_path):
      if authenticated_user_path and anonymous_user_path:
        raise ValueError("Doesnt make sense to have anonymous_user_path=True and authenticated_user_path=True")

      if anonymous_user_path:
        return None

      # Either use a new boto session using the active AWS profile
      # or the boto session belonging to the assumed role
      # Update 2019-12-13 actually, if it's
      import boto3
      boto_session=self.boto3_session if authenticated_user_path else boto3.session.Session()

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
      auth = MyBotoAWSRequestsAuth(aws_host=BASE_HOST,
                                    aws_region='us-east-1',
                                    aws_service='execute-api',
                                    boto_session=boto_session
                                    )

      # done
      return auth


  def request(self, method, relative_url, payload_json, authenticated_user_path=True, anonymous_user_path=False):
      """
      Wrapper to the URL request
      method - post
      relative_url - eg ./tags/suggest
      payload_json - "json" field for request call
      authenticated_user_path - False if can use the current local user
                                True if need to use the isitfit-api-provided role
                                Flag for self.register which can disable this as it doesn't have a account/user prefix in the URL

      anonymous_user_path - False if endpoint needs to get the AWS user information (requires execute-api permissions)
                            True if endpoint can be done by requests library without any AWS info

      anonymous_user_path was introduced for the /share/email endpoint
      - which is different than the older /account/user/share/email endpoint
      - because some users used the root account
      - Also some users dont have the execute-api permission

      The combination anonymous_user_path=True and authenticated_user_path=True is not allowed
      - the other combinations make sense
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


      # mark timestamp right before request (used in listen_sqs for dropping stale messages)
      import datetime as dt
      dt_now = dt.datetime.utcnow() #.strftime('%s')

      # make actual request
      import requests
      auth = self._get_auth(authenticated_user_path, anonymous_user_path)
      r1 = requests.request(method, absolute_url, json=payload_json, auth=auth)
      #logger.debug("python requests http request header:")
      #logger.debug(r1.request.headers)

      # https://stackoverflow.com/questions/18810777/how-do-i-read-a-response-from-python-requests
      import json
      r2 = json.loads(r1.text)

      # check AWS-generated errors (lambda?)
      if 'message' in r2:
        if r2['message']=='Internal server error':
          raise IsitfitCliError('Internal server error', self.ctx)
        else:
          # print(r2)
          raise IsitfitCliError('Serverside error #2: %s'%r2['message'], self.ctx)

      # AWS API Gateway error
      if 'Message' in r2:
        raise IsitfitCliError("Serverside error #3: %s"%r2['Message'], self.ctx)

      # validate schema of response
      register_schema_2 = Schema({
        'isitfitapi_status': {
            'code': str,
            'description': str,
        },
        'isitfitapi_body': {
          Optional(str): object
        }
      })
      try:
        register_schema_2.validate(r2)
      except SchemaError as e:
        import json
        logger.error("Received response: %s"%json.dumps(r2))
        raise IsitfitCliError("Does not match expected schema: %s"%str(e), self.ctx)

      # check for isitfit errors (in schema)
      if r2['isitfitapi_status']['code'] == 'error in schema':
        # print(r2)
        logger.debug("Detailed schema error message")
        logger.debug(r2['isitfitapi_status']['description'])
        raise IsitfitCliError("The data sent to the server by isitfit does not match the expected format.", self.ctx)

      # check for isitfit errors (general)
      elif r2['isitfitapi_status']['code'] == 'error':
        # print(r2)
        raise IsitfitCliError('Serverside error #1: %s'%r2['isitfitapi_status']['description'], self.ctx)

      elif r2['isitfitapi_status']['code']=='Registration in progress':
        # do nothing. This will be handled by self.register
        # Also, note that from isitfit-api, only the /register can lead to this code
        pass

      elif r2['isitfitapi_status']['code']=='Email verification in progress':
        # do nothing. This will be handled by EmailMan
        # Also, note that from isitfit-api, only the /share/email can lead to this code
        pass

      # check for isitfit unknown codes (i.e. maybe CLI is too old)
      elif r2['isitfitapi_status']['code'] != 'ok':
        # print(r2)
        msg = 'Unknown status code: %s. Description: %s'%(r2['isitfitapi_status']['code'], r2['isitfitapi_status']['description'])
        raise IsitfitCliError(msg, self.ctx)

      # if ok
      return r2, dt_now


  def listen_sqs(self, expected_type, dt_now):
    """
    expected_type - value of field "type" in the SQS messages to target
    dt_now - timestamp right before issuing the http that could have triggered the SQS messages
             Used to drop "stale" messages from earlier/canceled runs
    """
    # now listen on sqs

    # https://github.com/jegesh/python-sqs-listener/blob/master/sqs_listener/__init__.py#L123
    logger.debug("Waiting for results")
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
        #logger.debug("Sleep %i seconds"%n_secs)
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
