import click
from isitfit.cli.click_descendents import IsitfitCommand, isitfit_group

@isitfit_group(help="Manage migrations for local files (useful for debugging)", invoke_without_command=False, hidden=True)
@click.pass_context
def migrations(ctx):
  # FIXME click bug: `isitfit command subcommand --help` is calling the code in here. Workaround is to check --help and skip the whole section
  import sys
  if '--help' in sys.argv: return

  # usage stats
  from isitfit.utils import ping_matomo
  ping_matomo("/migrations")

  from isitfit.migrations.migman import MigMan
  migman = MigMan()
  migman.connect()
  migman.read()

  ctx.obj['migman'] = migman


@migrations.command(help="Show all migrations", cls=IsitfitCommand)
@click.pass_context
def show(ctx):
  # usage stats
  from isitfit.utils import ping_matomo
  ping_matomo("/migrations/show")

  migman = ctx.obj['migman']

  if migman.df_mig.shape[0]==0:
    click.echo("No pending migrations")
  else:
    click.echo("Pending migrations")
    click.echo(migman.df_mig[['migname', 'description']])
    click.echo("")
    click.secho("Use `isitfit migrations migrate` to execute them", fg="yellow")


@migrations.command(help="Execute pending migrations", cls=IsitfitCommand)
@click.option('--not-dry-run', is_flag=True, help='Simulate the migration without executing it')
@click.pass_context
def migrate(ctx, not_dry_run):
  # usage stats
  from isitfit.utils import ping_matomo, b2l
  ping_matomo("/migrations/migrate?not_dry_run=%s"%b2l(not_dry_run))

  migman = ctx.obj['migman']
  migman.not_dry_run = not_dry_run
  migman.migrate_all()

  if not not_dry_run:
    click.echo("")
    click.secho("This was a simulated execution", fg="yellow")
    click.secho("Repeat using `isitfit migrations migrate --not-dry-run` for actual execution", fg='yellow')
