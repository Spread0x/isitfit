import click


def pingOnError(ctx, error):
  # check if the error's ping was done
  didPing = 'unhandled_error_pinged' in ctx.obj.keys()
  if didPing: return

  from isitfit.utils import ping_matomo
  exception_type = type(error).__name__ # https://techeplanet.com/python-catch-all-exceptions/
  ping_matomo("/error/unhandled/%s?message=%s"%(exception_type, str(error)))

  # save a flag saying that the error sent a ping
  # Note that it is not necessary to do more than that, such as storing a list of pinged errors,
  # because there will be exactly one error raise at most before the program fails
  ctx.obj['unhandled_error_pinged'] = True


class IsitfitGroup(click.Group):
  """
  Wraps the click.Group.invoke function to ping matomo about the error before bubbling all exceptions
  """
  def invoke(self, ctx):
    try:
      ret = super().invoke(ctx)
      return ret
    except Exception as error:
      pingOnError(ctx, error)
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
      pingOnError(ctx, error)
      raise


def isitfit_group(name=None, **attrs):
  """
  Overrides click.decorators.group to use the class IsitfitGroup
  """
  attrs.setdefault('cls', IsitfitGroup)
  return click.command(name, **attrs)


# Inherit from click's usageError since click can handle it automatically
# https://click.palletsprojects.com/en/7.x/exceptions/
class IsitfitCliError(click.UsageError):
  """
  Inherited from click.exceptions.UsageError
  because it adds the context as a constructor argument,
  which I need for checking "is_outdated"
  https://github.com/pallets/click/blob/8df9a6b2847b23de5c65dcb16f715a7691c60743/click/exceptions.py#L51
  """

  # exit code
  exit_code = 10

  # constructor parameters from
  # https://github.com/pallets/click/blob/8df9a6b2847b23de5c65dcb16f715a7691c60743/click/exceptions.py#L11
  def show(self, file=None):
    # ping matomo about error
    ping_matomo("/error?message=%s"%self.message)

    # continue
    from click._compat import get_text_stderr
    if file is None:
        file = get_text_stderr()

    # echo wrap
    color = 'red'
    def wrapecho(message):
      # from click.utils import echo
      # echo('Error: %s' % self.format_message(), file=file, color=color)

      click.secho(message, fg=color)

    # main error
    wrapecho('Error: %s' % self.format_message())

    # if isitfit installation is outdated, append a message to upgrade
    if self.ctx is not None:
      if self.ctx.obj.get('is_outdated', None):
        hint_1 = "Upgrade your isitfit installation with `pip3 install --upgrade isitfit` and try again."
        wrapecho(hint_1)

    # add link to github issues
    hint_2 = "If the problem persists, please report it at https://github.com/autofitcloud/isitfit/issues/new"
    wrapecho(hint_2)

