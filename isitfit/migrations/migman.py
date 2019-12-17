from isitfit.utils import logger


import click
from isitfit.cli.click_descendents import IsitfitCliError
import pandas as pd


class MigMan:
  """
  Class that manages a local sqlite database to keep track of migrations that were already run
  https://www.pythoncentral.io/introduction-to-sqlite-in-python/
  """
  def __init__(self):
    self.quiet = False
    self.not_dry_run = False

    from isitfit.dotMan import DotMan
    import os
    self.db_p = os.path.join(DotMan().get_dotisitfit(), "migrations.sqlite")
    import datetime as dt
    self.dt_now = dt.datetime.now().date()
    

  def connect(self):
    import sqlite3
    self.db_h = sqlite3.connect(self.db_p)

  def _current(self):
    # Append new migrations here after implementing them as a function with a docstring in miglist.py
    from isitfit.migrations import miglist
    return [
      ('mig20191203a', miglist.mig20191203a),
      ('mig20191203b', miglist.mig20191203b),
      ('mig20191203c', miglist.mig20191203c),
    ]

  def __exit__(self):
    self.db_h.close()

  def _create(self):
    # Note: using migname instead of name because "name" is used in pandas as the "name of the row"
    cursor = self.db_h.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS migrations(
      migname TEXT PRIMARY KEY,
      executed DATE
    )
    ''')
    self.db_h.commit()

  def read(self):
    # in case of first run
    self._create()

    # insert "new" migrations
    df_mer = self._insertNew()

    # append docstrings
    df_mer['description'] = df_mer.func.apply(lambda x: x.__doc__.strip() if x.__doc__ is not None else None)

    logger.debug("Migrations")
    logger.debug(df_mer[['migname', 'executed', 'description']])

    # subset for those that don't have an executed date yet
    df_mer = df_mer[df_mer.executed.isna()]

    # save
    self.df_mig = df_mer



  def _insertNew(self):
    # migrations in local database
    df_db = pd.read_sql_query("select * from migrations", self.db_h)

    # full list of migrations
    df_py = pd.DataFrame(self._current(), columns=['migname', 'func'])

    # join. Note the left join will drop from the database any migrations that are deleted from self._current
    df_mer = df_py.merge(df_db, on='migname', how='left')

    # save to db
    df_mer[['migname', 'executed']].to_sql('migrations', self.db_h, if_exists='replace')

    # done
    return df_mer


  def migrate_all(self):
    if self.df_mig.shape[0]==0:
      if self.quiet: return
      raise IsitfitCliError("No migrations to execute")

    for i in range(self.df_mig.shape[0]):
      self._migrate_single(i)


  def _migrate_single(self, i):
    mig_i = self.df_mig.iloc[i]

    prefix = "" if self.not_dry_run else "[Dry run] "

    if not self.quiet:
      click.echo("%sExecuting migration: %s: %s"%(prefix, mig_i.migname, mig_i.description))

    if self.not_dry_run:
      mig_i.func()
      # no need to update local dataframe
      # self.df_mig.iloc[i, self.df_mig.columns == 'executed'] = self.dt_now

      # update row in database (per migration in case of error halfway)
      cursor = self.db_h.cursor()
      cursor.execute('''
      UPDATE migrations
      SET executed = ?
      where migname = ?
      ''', (self.dt_now, mig_i.migname, ))
      self.db_h.commit()



#-----------------------------
# utility functions
#def prompt_migrate():
#  migman = MigMan()
#  migman.connect()
#  migman.read()
#  if migman.df_mig.shape[0]==0:
#    return
#
#  raise IsitfitCliError("There are %i migrations that need to be executed. Please use `isitfit migrations show` to list them"%migman.df_mig.shape[0])



def silent_migrate():
  migman = MigMan()
  migman.quiet = True
  migman.not_dry_run = True
  migman.connect()
  migman.read()
  migman.migrate_all() 
  return migman.df_mig.migname.tolist()
