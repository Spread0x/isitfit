from .apiMan import ApiMan
import json
import logging
logger = logging.getLogger('isitfit')

from .utils import IsitfitCliError

class EmailMan:

  def __init__(self, dataType, dataVal, ctx):
    self.dataType = dataType
    self.dataVal = dataVal
    self.ctx = ctx
    self.api_man = ApiMan(tryAgainIn=1, ctx=ctx)

  def send(self, share_email):
    # get resources available
    self.api_man.register()

    # submit POST http request
    response_json, dt_now = self.api_man.request(
      method='post',
      relative_url='./share/email',
      payload_json={
        'dataType': self.dataType,
        'dataVal': self.dataVal,
        'share_email': share_email
      }
    )

    # check if error
    if response_json['isitfitapi_status']['code']=='Email verification in progress':
        raise IsitfitCliError(response_json['isitfitapi_status']['description'], self.ctx)

    if response_json['isitfitapi_status']['code']=='error':
        raise IsitfitCliError(response_json['isitfitapi_status']['description'], self.ctx)

    if response_json['isitfitapi_status']['code']!='ok':
        response_str = json.dumps(response_json)
        raise IsitfitCliError("Unsupported response from server: %s"%response_str, self.ctx)

    # validate schema
    from schema import SchemaError, Schema, Optional
    register_schema_2 = Schema({
        'from': str,
        Optional(str): object
      })
    try:
        register_schema_2.validate(response_json['isitfitapi_body'])
    except SchemaError as e:
        responseBody_str = json.dumps(response_json['isitfitapi_body'])
        err_msg = "Received response body: %s. Schema error: %s"%(responseBody_str, str(e))
        raise IsitfitCliError(err_msg, self.ctx)

    # otherwise proceed
    emailFrom = response_json['isitfitapi_body']['from']
    logger.info("Email sent from %s to: %s"%(emailFrom, ", ".join(share_email)))
    return

