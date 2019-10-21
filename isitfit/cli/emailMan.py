from ..apiMan import ApiMan
import json
import logging
logger = logging.getLogger('isitfit')

class EmailMan:

  def __init__(self, dataType, dataVal):
    self.dataType = dataType
    self.dataVal = dataVal
    self.api_man = ApiMan(tryAgainIn=1)

  def send(self, share_email):
    # get resources available
    self.api_man.register()

    # submit POST http request
    response, dt_now = self.api_man.request(
      method='post',
      relative_url='./share/email',
      payload_json={
        'dataType': self.dataType,
        'dataVal': self.dataVal,
        'share_email': share_email
      }
    )
    logger.info("Result of share-email:")
    logger.info(json.dumps(response))
