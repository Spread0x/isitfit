import click

@click.group(help="Manage migrations for local files", invoke_without_command=False)
@click.pass_context
def migrations(ctx):
  from isitfit.migrations.migman import MigMan
  migman = MigMan()
  migman.connect()
  migman.read()

  ctx.obj['migman'] = migman


from isitfit.utils import IsitfitCommand

@migrations.command(help="Show all migrations", cls=IsitfitCommand)
@click.pass_context
def show(ctx):
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
  from isitfit.utils import ping_matomo
  ping_matomo("/migrations/migrate?not_dry_run=%s"%not_dry_run)

  migman = ctx.obj['migman']
  migman.not_dry_run = not_dry_run
  migman.migrate_all()

  if not not_dry_run:
    click.echo("")
    click.secho("This was a simulated execution", fg="yellow")
    click.secho("Repeat using `isitfit migrations migrate --not-dry-run` for actual execution", fg='yellow')
