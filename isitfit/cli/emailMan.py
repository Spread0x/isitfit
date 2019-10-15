from ..apiMan import ApiMan

class EmailMan:

  def __init__(self, dataType, dataVal):
    self.dataType = dataType
    self.dataVal = dataVal
    self.api_man = ApiMan()

  def send(self, to_email):
    # get resources available
    self.api_man.register()

    # submit http request
    self.api_man.request(
      method='post',
      relative_url='./cost/analyze/email',
      payload_json={
        'dataType': self.dataType,
        'dataVal': self.dataVal,
        'to_email': to_email
      },
      response_schema=None
    )

#    # listen on SQS
#    for m in self.api_man.listen_sqs('cost analyze email'):
#      if m is None: break
#
#    # if got here, then didn't receive ack
#    raise IsitfitError("Didn't receive ack from API for email")
