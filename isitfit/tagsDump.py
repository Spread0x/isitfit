import logging
logger = logging.getLogger('isitfit')

from .tagsSuggestBasic import TagsSuggestBasic
class TagsDump(TagsSuggestBasic):

  def tags_to_dict(self, ec2_obj):
    tags_dict = {x['Key']: x['Value'] for x in ec2_obj.tags}
    return tags_dict


  def suggest(self):
      logger.info("Dumping to csv")
      from .tagsSuggestBasic import dump_df_to_csv
      self.csv_fn = dump_df_to_csv(self.tags_df, 'isitfit-tags-dump-')


  def display(self):
    from .utils import display_df
    display_df(
      "Dumped tags:",
      self.tags_df,
      self.csv_fn,
      self.tags_df.shape,
      logger
    )
