import click


def pingOnError(error):
  from isitfit.utils import ping_matomo
  exception_type = type(error).__name__ # https://techeplanet.com/python-catch-all-exceptions/
  ping_matomo("/error/unhandled/%s?message=%s"%(exception_type, str(error)))


class IsitfitGroup(click.Group):
  """
  Wraps the click.Group.invoke function to ping matomo about the error before bubbling all exceptions
  """
  def invoke(self, ctx):
    try:
      ret = super().invoke(ctx)
      return ret
    except Exception as error:
      pingOnError(error)
      raise


from isitfit.utils import display_footer

class IsitfitCommand(click.Command):
  """
  Wraps the click.Command.invoke function to ping matomo about the error before bubbling all exceptions

  Also Call display_footer at the end of each invokation
    https://github.com/pallets/click/blob/8df9a6b2847b23de5c65dcb16f715a7691c60743/click/core.py#L945
  """
  def invoke(self, ctx):
    try:
      ret = super().invoke(ctx)
      display_footer()
      return ret
    except Exception as error:
      pingOnError(error)
      raise


def isitfit_group(name=None, **attrs):
  """
  Overrides click.decorators.group to use the class IsitfitGroup
  """
  attrs.setdefault('cls', IsitfitGroup)
  return click.command(name, **attrs)
