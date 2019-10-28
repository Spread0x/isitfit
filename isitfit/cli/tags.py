import logging
logger = logging.getLogger('isitfit')

import click

from ..utils import IsitfitCommand

@click.group(help="Explore EC2 tags", invoke_without_command=False)
def tags():
  pass



@tags.command(help="Generate new tags suggested by isitfit for each EC2 instance", cls=IsitfitCommand)
@click.option('--advanced', is_flag=True, help='Get advanced suggestions of tags. Requires login')
@click.pass_context
def suggest(ctx, advanced):
  # gather anonymous usage statistics
  from ..utils import ping_matomo, IsitfitCliError
  ping_matomo("/tags/suggest")

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
  from ..utils import ping_matomo, IsitfitCliError
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
  from ..utils import ping_matomo, IsitfitCliError
  ping_matomo("/tags/push")

  from ..tags.tagsPush import TagsPush

  tp = TagsPush(csv_filename, ctx)

  tp.read_csv()
  tp.validateTagsFile()
  tp.pullLatest()
  tp.diffLatest()
  tp.processPush(not not_dry_run)

