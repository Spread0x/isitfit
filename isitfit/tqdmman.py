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
  def __init__(self, ctx):
    self.show = not(ctx.obj['debug'] or ctx.obj['verbose'])


class TqdmL2Verbose(TqdmL2Base):
  def __init__(self, ctx):
    self.show = ctx.obj['debug'] or ctx.obj['verbose']



