import logging
logger = logging.getLogger('isitfit')


def dump_df_to_csv(df_dump, csv_prefix):
    import tempfile
    import pandas as pd

    # https://pypi.org/project/termcolor/
    from termcolor import colored

    with tempfile.NamedTemporaryFile(prefix=csv_prefix, suffix='.csv', delete=False) as fh:
      logger.info(colored("Dumping data into %s"%fh.name, "cyan"))
      df_dump.to_csv(fh.name, index=False)
      return fh.name



class TagsSuggestBasic:

  def __init__(self):
    logger.debug("TagsSuggestBasic::constructor")
    # boto3 ec2 and cloudwatch data
    import boto3
    self.ec2_resource = boto3.resource('ec2')
    self.tags_list = []
    self.tags_df = None

  def prepare(self):
    logger.debug("TagsSuggestBasic::prepare")
    pass

  def tags_to_dict(self, ec2_obj):
    tags_dict = {x['Key']: x['Value'] for x in ec2_obj.tags if x['Key']=='Name'}
    return tags_dict

  def fetch(self):
    logger.debug("TagsSuggestBasic::fetch")
    logger.info("Counting EC2 instances")
    n_ec2_total = len(list(self.ec2_resource.instances.all()))
    msg_total = "Found a total of %i EC2 instances"%n_ec2_total
    if n_ec2_total==0:
      from .utils import IsitfitError
      raise IsitfitError(msg_total)

    logger.warning(msg_total)

    self.tags_list = []
    from tqdm import tqdm
    desc = "Scanning EC2 instances"
    ec2_all = self.ec2_resource.instances.all()
    for ec2_obj in tqdm(ec2_all, total=n_ec2_total, desc=desc, initial=1):
      if ec2_obj.tags is None:
        tags_dict = {}
      else:
        tags_dict = self.tags_to_dict(ec2_obj)

      tags_dict['instance_id'] = ec2_obj.instance_id
      self.tags_list.append(tags_dict)

    # convert to pandas dataframe when done
    self.tags_df = self._list_to_df()


  def _list_to_df(self):
      logger.info("Converting tags list into dataframe")
      import pandas as pd
      df = pd.DataFrame(self.tags_list)
      df = df.rename(columns={'instance_id': '_0_instance_id', 'Name': '_1_Name'}) # trick to keep instance ID and name as the first columns
      df = df.sort_index(axis=1)  # sort columns
      df = df.rename(columns={'_0_instance_id': 'instance_id', '_1_Name': 'Name'}) # undo trick
      return df


  def suggest(self):
      logger.debug("TagsSuggestBasic::suggest")
      logger.info("Generating suggested tags")
      from .tagsImplier import TagsImplierMain
      tags_implier = TagsImplierMain(self.tags_df)
      self.suggested_df = tags_implier.imply()
      self.csv_fn = dump_df_to_csv(self.suggested_df, 'isitfit-tags-suggestBasic-')
      self.suggested_shape = self.suggested_df.shape


  def display(self):
    logger.debug("TagsSuggestBasic::display")
    from .utils import display_df
    display_df(
      "Suggested tags:",
      self.suggested_df,
      self.csv_fn,
      self.suggested_shape,
      logger
    )
