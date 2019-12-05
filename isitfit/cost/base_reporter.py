# Related
# https://docs.datadoghq.com/integrations/amazon_redshift/
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/redshift.html#Redshift.Paginator.DescribeClusters

from termcolor import colored
import click

from isitfit.utils import logger



class ReporterBase:
  def postprocess(self, context_all):
    raise Exception("To be implemented by derived class")

  def display(self, context_all):
    raise Exception("To be implemented by derived class")

  def _promptToEmailIfNotRequested(self, emailTo):
    from isitfit.utils import ping_matomo

    if emailTo is not None:
      if len(emailTo) > 0:
        # user already requested email
        ping_matomo("/cost/share_email?original=T")
        return emailTo

    #from isitfit.utils import IsitfitCliError

    # more quick validation
    # works with a@b.c but not a@b@c.d
    # https://stackoverflow.com/questions/8022530/how-to-check-for-valid-email-address#8022584
    import re
    EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")

    # prompt for email
    while True:
      # use "default=''" so that the "leave blank to skip" works (instead of click re-prompting until it gets a value)
      res_prompt = click.prompt('Email to which to share the results (leave blank to skip)', type=str, default='')

      # check if blank
      res_prompt = res_prompt.strip()
      if res_prompt=='':
        ping_matomo("/cost/share_email?original=F&provided=F")
        return None

      # quick validate
      # shortest email is: a@b.c
      # Longest email is: shadishadishadishadi@shadishadishadishadi.shadi
      if len(res_prompt) >= 5:
        if len(res_prompt) <= 50:
          if bool(EMAIL_REGEX.match(res_prompt)):
            ping_matomo("/cost/share_email?original=F&provided=T")
            return [res_prompt]

      # otherwise, invalid email
      logger.error("Invalid email address: %s"%res_prompt)


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
      emailTo = self._promptToEmailIfNotRequested(emailTo)

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






