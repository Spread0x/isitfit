"""
Classes to help with managing visibility of tqdm progress bars at different levels of the code
https://github.com/tqdm/tqdm/
"""

class TqdmL2Base:
  def __init__(self):
    # override to display tqdm
    self.show = False

  def __call__(self, iterator, *args, **kwargs):
    if not self.show:
      return iterator

    from tqdm import tqdm
    return tqdm(iterator, *args, **kwargs)


class TqdmL2Quiet(TqdmL2Base):
  """
  Sets show=True when isitfit used without --verbose nor --debug, i.e. isitfit cost analyze
  Useful for showing a service-level progressbar, i.e. moves by 1 for ec2, then 1 for redshift, etc
  The problem is that currently only ec2 and redshift are supported,
  which makes this progressbar lose its meaning.
  """
  def __init__(self, ctx):
    # FIXME update 2019-12-09
    #   Until I build a meaningful progressbar at the level of services,
    #   this progressbar is getting completely disabled.
    # self.show = not(ctx.obj['debug'] or ctx.obj['verbose'])
    self.show = False


class TqdmL2Verbose(TqdmL2Base):
  """
  Sets show=True when isitfit used with either --verbose or --debug, i.e. isitfit --verbose cost analyze
  """
  def __init__(self, ctx):
    # FIXME update 2019-12-09
    # Related to the note in TqdmL2Quiet, this progressbar is getting enabled now all the time, until a proper service-level progress bar is implemented
    # self.show = ctx.obj['debug'] or ctx.obj['verbose']
    self.show = True

