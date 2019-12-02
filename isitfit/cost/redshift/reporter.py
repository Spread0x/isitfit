# Related
# https://docs.datadoghq.com/integrations/amazon_redshift/
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/redshift.html#Redshift.Paginator.DescribeClusters

from termcolor import colored
import click

import logging
logger = logging.getLogger('isitfit')


class ReporterBase:
  def postprocess(self, context_all):
    raise Exception("To be implemented by derived class")

  def display(self, context_all):
    raise Exception("To be implemented by derived class")

  def _promptToEmailIfNotRequested(self, emailTo):
    if emailTo is not None:
      if len(emailTo) > 0:
        # user already requested email
        return emailTo

    # prompt user if to email
    click.echo("")
    res_conf = click.confirm("Would you like to share the results to your email?")
    if not res_conf:
      return None

    #from isitfit.utils import IsitfitCliError

    # more quick validation
    # works with a@b.c but not a@b@c.d
    # https://stackoverflow.com/questions/8022530/how-to-check-for-valid-email-address#8022584
    import re
    EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")

    # prompt for email
    while True:
      res_prompt = click.prompt('Please enter a valid email address (leave blank to skip)', type=str)

      # check if blank
      if res_prompt=='':
        return None

      # quick validate
      # shortest email is: a@b.c
      # Longest email is: shadishadishadishadi@shadishadishadishadi.shadi
      if len(res_prompt) >= 5:
        if len(res_prompt) <= 50:
          if bool(EMAIL_REGEX.match(res_prompt)):
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






class ReporterOptimize(ReporterBase):
  def postprocess(self, context_all):
    # unpack
    self.analyzer = context_all['analyzer']

    # proceed
    analyze_df = self.analyzer.analyze_df
    analyze_df['CpuMaxMax'] = analyze_df['CpuMaxMax'].fillna(value=0).astype(int)
    analyze_df['CpuMinMin'] = analyze_df['CpuMinMin'].fillna(value=0).astype(int)

    # copied from isitfit.cost.optimizationListener.storecsv...
    import tempfile
    with tempfile.NamedTemporaryFile(prefix='isitfit-full-redshift-', suffix='.csv', delete=False) as  csv_fh_final:
      self.csv_fn_final = csv_fh_final.name
      click.echo(colored("Saving final results to %s"%csv_fh_final.name, "cyan"))
      analyze_df.to_csv(csv_fh_final.name, index=False)
      click.echo(colored("Save complete", "cyan"))

    # save in context for aggregator
    context_all['csv_fn_final'] = self.csv_fn_final

    return context_all


  def display(self, context_all):
    # copied from isitfit.cost.optimizationListener.display_all
    analyze_df = self.analyzer.analyze_df

    # display dataframe
    from ...utils import display_df
    display_df(
      "Redshift cluster classifications",
      analyze_df,
      self.csv_fn_final,
      analyze_df.shape,
      logger
    )
    return context_all


  def email(self, context_all):
      # silently return
      # raise Exception("Error emailing optimization: Not yet implemented")
      return context_all
