from .utils import IsitfitError

import logging
logger = logging.getLogger('isitfit')

# https://pypi.org/project/termcolor/
from termcolor import colored

class TagsCsvDiff:

  def __init__(self, df_old, df_new):
    """
    df_old - pandas dataframe representing old tags
    df_new - new tags (pd dataframe)
    """
    self.df_old = df_old
    self.df_new = df_new
    self.old_minus_new = set()
    self.new_minus_old = set()
    self.migrations = []

  def noChanges(self):
    """
    Fast way to identify that no changes
    """
    to_json = lambda x: x.sort_values('instance_id', ascending=True)[sorted(list(x.columns))].to_json(orient='records')
    json_old = to_json(self.df_old)
    json_new = to_json(self.df_new)
    if json_old == json_new:
      raise IsitfitError("Aborting `tags push` due to no changes detected.")

  def noNewInstances(self):
    inst_old = set(self.df_old.instance_id)
    inst_new = set(self.df_new.instance_id)
    inst_created = inst_new - inst_old
    inst_created = sorted(list(inst_created))
    if len(inst_created)>0:
      msg_1 = "Found new instances IDs: %s%s"
      msg_2 = ", ".join(inst_created[:5])
      msg_3 ="..." if len(inst_created)>5 else ""
      msg_4 = msg_1%(msg_2,msg_3)
      raise IsitfitError(msg_4)


  def getDiffCols(self):
    # diff columns
    old_cols = set(self.df_old.columns)
    new_cols = set(self.df_new.columns)
    self.old_minus_new = old_cols - new_cols
    self.new_minus_old = new_cols - old_cols

  def renamedTags(self):
    # calculate string distances of all differences
    # https://stackoverflow.com/a/31236578/4126114
    # https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.corr.html
    import difflib
    corr_method = lambda s1, s2: 1 if s1 in s2 else (difflib.SequenceMatcher(None, s1, s2).ratio())
    import pandas as pd
    import numpy as np
    col_dist = pd.DataFrame(
      np.zeros(shape=(
          len(self.old_minus_new),
          len(self.new_minus_old)
        )),
      index=self.old_minus_new,
      columns=self.new_minus_old
    )
    new_processed = set()
    old_processed = set()
    for c1 in self.old_minus_new:
      for c2 in self.new_minus_old:
        d12 = corr_method(c1, c2)
        col_dist.loc[c1, c2] = d12

      # find best match
      d1_maxD = col_dist.loc[c1].max()
      if d1_maxD > 0.7:
        d1_maxV = col_dist.loc[c1].idxmax()
        confirm_msg = colored('Did you rename the tag "%s" to "%s"? yes/[no] '%(c1, d1_maxV), 'cyan')
        confirm_mv = input(confirm_msg)
        if confirm_mv.lower() in ['y', 'yes']:
          mig_i = ('mv', c1, d1_maxV)
          self.migrations.append(mig_i)
          old_processed.add(c1)
          new_processed.add(d1_maxV)

    # remove processed entries
    self.new_minus_old -= new_processed
    self.old_minus_new -= old_processed


  def newTags(self):
    """
    Identify if some tags are completely new.
    """
    if len(self.new_minus_old)==0:
      return

    #msg = []
    #msg.append("The following tags are completely new:")
    #msg = msg + sorted(list(self.new_minus_old))
    #msg = "\n".join(msg)
    #logger.info(msg)
    #logger.info("")

    logger.info("Found %i new tag(s)"%len(self.new_minus_old))
    logger.info("")

    new_processed = set()
    for ni in self.new_minus_old:
      confirm_msg = colored('Did you add the tag "%s"? yes/[no] '%ni, 'cyan')
      confirm_new = input(confirm_msg)
      if confirm_new.lower() in ['y', 'yes']:
        mig_i = ('touch', None, ni)
        self.migrations.append(mig_i)
        new_processed.add(ni)

    # remove all processed
    self.new_minus_old -= new_processed

  def droppedTags(self):
    """
    Identify if some tags are completely dropped.
    Ask the user if indeed dropped, or accident.
    Follows the idea of django/db/migrations/questioner.py
    where django asks if fields are renamed or dropped
    https://github.com/django/django/blob/e90af8bad44341cf8ebd469dac57b61a95667c1d/django/db/migrations/questioner.py
    """
    if len(self.old_minus_new)==0:
      return

    #msg = []
    #msg.append("The following tags are no longer present:")
    #msg = msg + sorted(list(self.old_minus_new))
    #msg = "\n".join(msg)
    #logger.info(msg)
    #logger.info("")

    logger.info("There are %i deleted tag(s)"%len(self.old_minus_new))
    logger.info("")

    old_processed = set()
    for ni in self.old_minus_new:
      confirm_msg = colored('Did you completely delete the tag "%s"? yes/[no] '%ni, 'cyan')
      confirm_del = input(confirm_msg)
      if confirm_del.lower() in ['y', 'yes']:
        mig_i = ('rm', ni, None)
        self.migrations.append(mig_i)
        old_processed.add(ni)

    # remove all processed
    self.old_minus_new -= old_processed


  def anyRemaining(self):
    if len(self.new_minus_old)>0:
      msg_1 = "Aborting `tags push` due to new tags in pushed csv file, and user indicated they shouldnt be created"
      msg_2 = ", ".join(sorted(list(self.new_minus_old)))
      msg_3 = "%s: %s"%(msg_1,msg_2)
      raise IsitfitError(msg_3)

    if len(self.old_minus_new)>0:
      msg_1 = "Aborting `tags push` due to missing tags in pushed csv file, and user indicated they shouldnt be deleted"
      msg_2 = ", ".join(sorted(list(self.old_minus_new)))
      msg_3 = "%s: %s"%(msg_1,msg_2)
      raise IsitfitError(msg_3)
