from .apiMan import ApiMan
import json
from isitfit.utils import logger


from isitfit.cli.click_descendents import IsitfitCliError




class EmailMan:

  def __init__(self, dataType, dataVal, ctx):
    self.dataType = dataType
    self.dataVal = dataVal
    self.ctx = ctx
    self.api_man = ApiMan(tryAgainIn=1, ctx=ctx)
    self.try_again = 3 # max attempts to try again

    # for set/get last used email
    from isitfit.dotMan import DotLastEmail
    self.last_email = DotLastEmail()


  def _send_core(self, share_email):
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
    return response_json, dt_now


  def send(self, share_email):
    logger.info("Sending email")

    # pre-process spaces if any
    share_email = [x.strip() for x in share_email]

    # save 1st entry as "last email"
    self.last_email.set(share_email[0])

    # get resources available
    self.api_man.register()

    # submit POST http request
    response_json, dt_now = self._send_core(share_email)

    # check response status

    # Update 2019-12-12 Instead of raising an exception and aborting,
    # show the user a prompt to check his/her email
    # and give the program a chance to re-send the email
    import click
    while (
        (response_json['isitfitapi_status']['code']=='Email verification in progress')
        and (self.try_again > 0)
      ):
        click.prompt('A verification link was emailed to you now. Please click the link, then press Enter here to continue', default='Enter')
        self.try_again -= 1
        response_json, dt_now = self._send_core(share_email)

    if self.try_again==0:
        raise IsitfitCliError(response_json['isitfitapi_status']['description'], self.ctx)

    # Update 2019-12-12 This code will get handled by apiMan and will never arrive here, so commenting it out
    #if response_json['isitfitapi_status']['code']=='error':
    #    raise IsitfitCliError(response_json['isitfitapi_status']['description'], self.ctx)

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
    import click
    click.echo("Email sent from %s to: %s"%(emailFrom, ", ".join(share_email)))
    return

