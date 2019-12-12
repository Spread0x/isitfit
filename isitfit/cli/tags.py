from isitfit.utils import logger


import click

from isitfit.cli.click_descendents import IsitfitCommand, isitfit_group, isitfit_option_profile

@isitfit_group(help="Explore EC2 tags", invoke_without_command=False)
@isitfit_option_profile()
def tags(profile):
  # FIXME click bug: `isitfit command subcommand --help` is calling the code in here. Workaround is to check --help and skip the whole section
  import sys
  if '--help' in sys.argv: return

  # gather anonymous usage statistics
  from isitfit.utils import ping_matomo
  ping_matomo("/tags")

  pass



@tags.command(help="Generate new tags suggested by isitfit for each EC2 instance", cls=IsitfitCommand)
@click.option('--advanced', is_flag=True, help='Get advanced suggestions of tags. Requires login')
@click.pass_context
def suggest(ctx, advanced):
  # gather anonymous usage statistics
  from isitfit.utils import ping_matomo, b2l
  ping_matomo("/tags/suggest?advanced=%s"%b2l(advanced))

  tl = None
  if not advanced:
    from ..tags.tagsSuggestBasic import TagsSuggestBasic
    tl = TagsSuggestBasic(ctx)
  else:
    from ..tags.tagsSuggestAdvanced import TagsSuggestAdvanced
    tl = TagsSuggestAdvanced(ctx)

  tl.prepare()
  tl.fetch()
  tl.suggest()
  tl.display()


@tags.command(help="Dump existing EC2 tags in tabular form into a csv file", cls=IsitfitCommand)
@click.pass_context
def dump(ctx):
  # gather anonymous usage statistics
  from isitfit.utils import ping_matomo
  ping_matomo("/tags/dump")

  from ..tags.tagsDump import TagsDump
  tl = TagsDump(ctx)

  tl.fetch()
  tl.suggest() # not really suggesting. Just dumping to csv
  tl.display()



@tags.command(help="Push EC2 tags from csv file", cls=IsitfitCommand)
@click.argument('csv_filename') #, help='Path to CSV file holding tags to be pushed. Should match format from `isitfit tags dump`')
@click.option('--not-dry-run', is_flag=True, help='True for dry run (simulated push)')
@click.pass_context
def push(ctx, csv_filename, not_dry_run):
  # gather anonymous usage statistics
  from isitfit.utils import ping_matomo, b2l
  ping_matomo("/tags/push?csv_filename=%s&not_dry_run=%s"%(csv_filename, b2l(not_dry_run)))

  from ..tags.tagsPush import TagsPush

  tp = TagsPush(csv_filename, ctx)

  tp.read_csv()
  tp.validateTagsFile()
  tp.pullLatest()
  tp.diffLatest()
  tp.processPush(not not_dry_run)

