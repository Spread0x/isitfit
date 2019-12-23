# Related
# https://docs.datadoghq.com/integrations/amazon_redshift/
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/redshift.html#Redshift.Paginator.DescribeClusters

from termcolor import colored
import click

from isitfit.utils import logger



class ReporterBase:
  def __init__(self):
    self.emailTo = None

  def postprocess(self, context_all):
    raise Exception("To be implemented by derived class")

  def display(self, context_all):
    raise Exception("To be implemented by derived class")

  def email(self, context_all):
      """
      ctx - click context
      """
      for fx in ['dataType', 'dataVal']:
        if not fx in context_all:
          raise Exception("Missing field from context: %s. This function should be implemented by the derived class"%fx)

      # unpack
      emailTo, ctx = context_all['emailTo'], context_all['click_ctx']

      # prompt user for email if not requested
      if not ctx.obj['skip_prompt_email']:
        from isitfit.utils import PromptToEmailIfNotRequested
        pte = PromptToEmailIfNotRequested()
        emailTo = pte.prompt(emailTo)

      # check if email requested
      if emailTo is None:
          return context_all

      if len(emailTo)==0:
          return context_all

      from isitfit.emailMan import EmailMan
      em = EmailMan(
        dataType=context_all['dataType'], # ec2, not redshift
        dataVal=context_all['dataVal'],
        ctx=ctx
      )
      em.send(emailTo)

      return context_all






