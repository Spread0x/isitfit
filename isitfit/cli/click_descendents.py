import click


def pingOnError(ctx, error):
  # if not dict yet, i.e. before the cli.core.cli_core group
  # Important to keep track of the didPing variable
  if ctx.obj is None: return

  # check if the error's ping was done
  didPing = 'unhandled_error_pinged' in ctx.obj.keys()
  if didPing: return

  # send to sentry.io via isitfit.io (check usage of sentry_proxy in cli.core)
  from sentry_sdk import capture_exception
  capture_exception(error)

  # proceed to ping matomo about the error (to be deprecated in full in favor of sentry)
  from isitfit.utils import ping_matomo
  exception_type = type(error).__name__ # https://techeplanet.com/python-catch-all-exceptions/
  exception_str = ""
  try:
    exception_str = str(error)
  except:
    pass

  ping_matomo("/error/unhandled/%s?message=%s"%(exception_type, exception_str))

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
    from isitfit.utils import ping_matomo
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
      if self.ctx.obj is not None:
        if self.ctx.obj.get('is_outdated', None):
          hint_1 = "Upgrade your isitfit installation with `pip3 install --upgrade isitfit` and try again."
          wrapecho(hint_1)

    # add link to github issues
    hint_2 = "If the problem persists, please report it at https://github.com/autofitcloud/isitfit/issues/new"
    wrapecho(hint_2)



def isitfit_option_base(name=None, **attrs):
  """
  Overrides click.option due to trouble with options having prompt=True (or prompt='bla') and the --help call
  eg `isitfit cost analyze --help` was prompting for `--profile`
     `isitfit version` was also prompting for `--profile` when it was at the `cli_core` level

  This resolves click github issue: https://github.com/pallets/click/issues/295

  Original notes (no longer valid since problems solved with isitfit_option):
    --profile docs at
      https://click.palletsprojects.com/en/7.x/options/?highlight=prompt#values-from-environment-variables
    The first commented version with prompt=... is not possible to implement because in this case, `isitfit cost analyze --help` will also prompt for the profile
      (similar to the --ndays reason it was duplicated to the click.commands instead of keeping it at the click.group leve)
    Also, originally, this was in the cli.core.cli_core group,
      and eventhough Click has a "eager" option and even a "version_option", but I'm not using those ATM
      and the problem there was with `isitfit version` prompting for this.
    This time, with profile, unlike ndays, instead of duplicating it for each command,
      I'm implementing it manually if not provided
  """
  if not attrs.get('prompt'):
    # nothing special required
    return click.option(name, **attrs)

  # shortcuts
  callback_ori = attrs.get('callback')
  prompt_ori = attrs.get('prompt')
  default_ori = attrs.get('default')
  type_ori = attrs.get('type')

  # wrap callback_ori with manual prompt IF NO --help
  def callback_wrap(ctx, param, value):
    # check for --help
    import sys
    if '--help' in sys.argv:
      # no need to do anything
      return value

    if value is None:
      # manually prompt only if not already supplied
      value = click.prompt(prompt_ori, default=default_ori, type=type_ori)
    else:
      value = type_ori(value)

    # call the original callback
    if callback_ori is None: return value
    return callback_ori(ctx, param, value)

  # over-ride the originals since moved into callback_wrap
  attrs['callback'] = callback_wrap
  attrs['prompt'] = False
  attrs['default'] = None
  attrs['type'] = None

  # return the "corrected" option
  return click.option(name, **attrs)



def isitfit_option_profile(name=None, **attrs):
  """
  Special option dedicated to --profile
  Was worth it because it was in cli.tags and cli.cost
  """
  from isitfit.utils import AwsProfileMan
  profile_man = AwsProfileMan()

  ret_opt = isitfit_option_base('--profile', type=str, default=profile_man.default(), callback=profile_man.validate_profile, prompt=profile_man.prompt(), help='Use a specific profile from your credential file.', envvar='AWS_PROFILE')
  return ret_opt

