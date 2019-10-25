import logging
logger = logging.getLogger('isitfit')

import click

from ..utils import display_footer

@click.group(help="Explore EC2 tags", invoke_without_command=False)
def tags():
  pass



@tags.command(help="Generate new tags suggested by isitfit for each EC2 instance")
@click.option('--advanced', is_flag=True, help='Get advanced suggestions of tags. Requires login')
def suggest(advanced):
  # gather anonymous usage statistics
  from ..utils import ping_matomo, IsitfitCliError
  ping_matomo("/tags/suggest")

  tl = None
  if not advanced:
    from ..tags.tagsSuggestBasic import TagsSuggestBasic
    tl = TagsSuggestBasic()
  else:
    from ..tags.tagsSuggestAdvanced import TagsSuggestAdvanced
    tl = TagsSuggestAdvanced()

  try:
    tl.prepare()
    tl.fetch()
    tl.suggest()
    tl.display()
  except IsitfitCliError as e:
    logger.error("Error: %s"%str(e))
    import sys
    sys.exit(1)

  display_footer()


@tags.command(help="Dump existing EC2 tags in tabular form into a csv file")
def dump():
  # gather anonymous usage statistics
  from ..utils import ping_matomo, IsitfitCliError
  ping_matomo("/tags/dump")

  from ..tags.tagsDump import TagsDump
  tl = TagsDump()

  try:
    tl.fetch()
    tl.suggest() # not really suggesting. Just dumping to csv
    tl.display()
  except IsitfitCliError as e:
    logger.error("Error: %s"%str(e))
    import sys
    sys.exit(1)

  display_footer()



@tags.command(help="Push EC2 tags from csv file")
@click.argument('csv_filename') #, help='Path to CSV file holding tags to be pushed. Should match format from `isitfit tags dump`')
@click.option('--not-dry-run', is_flag=True, help='True for dry run (simulated push)')
def push(csv_filename, not_dry_run):
  # gather anonymous usage statistics
  from ..utils import ping_matomo, IsitfitCliError
  ping_matomo("/tags/push")

  from ..tags.tagsPush import TagsPush

  tp = TagsPush(csv_filename)
  try:
    tp.read_csv()
    tp.validateTagsFile()
    tp.pullLatest()
    tp.diffLatest()
    tp.processPush(not not_dry_run)
  except IsitfitCliError as e:
    logger.error("Error: %s"%str(e))
    import sys
    sys.exit(1)

  display_footer()

