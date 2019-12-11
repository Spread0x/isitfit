from isitfit.cli.click_descendents import IsitfitCliError

from isitfit.utils import logger


class TagsPush:
  """
  Class that will push a csv of tags to EC2
  Uses boto3's ResourceGroupsTaggingAPI
  for efficient "mass" tagging.
  https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/resourcegroupstaggingapi.html#ResourceGroupsTaggingAPI.Client.untag_resources
  https://docs.aws.amazon.com/resourcegroupstagging/latest/APIReference/API_UntagResources.html
  """

  def __init__(self, csv_fn, ctx):
    """
    csv_fn - filename of CSV file containing the tags
    ctx - click context object
    """
    self.csv_fn = csv_fn
    self.csv_df = None
    self.latest_df = None
    self.ctx = ctx

  def read_csv(self):
    import pandas as pd
    try:
      # read all fields as string
      self.csv_df = pd.read_csv(self.csv_fn, dtype=str)
    except pd.errors.EmptyDataError as e_info:
      raise IsitfitCliError("Error reading csv: %s"%str(e_info), self.ctx)

    if self.csv_df.shape[0]==0:
      raise IsitfitCliError("Tags csv file is empty", self.ctx)

    if 'instance_id' not in self.csv_df.columns:
      raise IsitfitCliError("Missing column instance_id", self.ctx)

    # sort by instance ID
    self.csv_df = self.csv_df.sort_values('instance_id', ascending=True)

    # fill na with ''
    self.csv_df = self.csv_df.fillna(value='')


  def validateTagsFile(self):
    if self.csv_df is None:
      raise IsitfitCliError("Internal dev error: Call TagsPush::read_csv before TagsPush::validateTagsFile", self.ctx)

    csv_dict = self.csv_df.to_dict(orient='records')
    from schema import Schema, Optional, SchemaError
    csv_schema = Schema([{
      'instance_id': str,
      'Name': str,
      Optional(str): str
    }])
    try:
      csv_schema.validate(csv_dict)
    except SchemaError as e:
      raise IsitfitCliError("CSV is not a tags file: %s"%str(e), self.ctx)

  def pullLatest(self):
    logger.info("Pulling latest tags for comparison")
    from .tagsDump import TagsDump
    td = TagsDump(self.ctx)
    td.fetch()
    td.suggest() # not really suggesting. Just dumping to csv
    self.latest_df = td.tags_df
    self.latest_df = self.latest_df.fillna(value='')

  def diffLatest(self):
    if self.latest_df is None:
      raise IsitfitCliError("Internal dev error: Call TagsPush::pullLatest before TagsPush::diffLatest", self.ctx)

    if self.csv_df is None:
      raise IsitfitCliError("Internal dev error: Call TagsPush::read_csv before TagsPush::diffLatest", self.ctx)

    # diff columns
    from .tagsCsvDiff import TagsCsvDiff
    td = TagsCsvDiff(self.latest_df, self.csv_df)
    td.noChanges()
    td.noNewInstances()
    td.getDiffCols()
    td.renamedTags()
    td.newTags()
    td.droppedTags()
    # print(td.migrations, td.old_minus_new, td.new_minus_old)
    td.anyRemaining()

    # get migrations
    import pandas as pd
    self.mig_df = pd.DataFrame(td.migrations, columns=['action', 'old', 'new'])
    logger.debug("")
    logger.debug("Tag migrations")
    if self.mig_df.shape[0]==0:
      logger.debug("None")
    else:
      logger.debug(self.mig_df)

    logger.debug("")

  def processPush(self, dryRun:bool):
    # max ec2 per call is 20
    # but just doing 1 at a time for now
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/resourcegroupstaggingapi.html#ResourceGroupsTaggingAPI.Client.tag_resources
    import boto3
    tagging_client = boto3.client('resourcegroupstaggingapi')
    ec2_resource = boto3.resource('ec2')
    account_id = boto3.client('sts').get_caller_identity()['Account']

    import json
    preproc = lambda x: x[sorted(list(x.columns))].set_index('instance_id')
    self.latest_df = preproc(self.latest_df)
    self.csv_df = preproc(self.csv_df)
    from tqdm import tqdm
    runType_prefix = "Dry run" if dryRun else "Live"
    for instance_id, row_new in tqdm(self.csv_df.iterrows(), total=self.csv_df.shape[0], desc="Tag CSV row (%s)"%runType_prefix, initial=1):
        row_old = self.latest_df.loc[instance_id]
        tags_new = row_new.to_dict()
        tags_old = row_old.to_dict()
        if tags_new==tags_old:
          logger.debug("Skipping %s since no changes"%instance_id)
          continue

        # keeping only changed keys
        keys_dotag = {}
        for k in tags_new:
          if not tags_new[k]:
            continue # empty tags are skipped

          if k not in tags_old:
            keys_dotag[k] = tags_new[k]
            continue

          if tags_new[k] != tags_old[k]:
            keys_dotag[k] = tags_new[k]
            continue

        # proceed with untagging
        keys_untag = []
        for k in tags_old:
          if not tags_old[k]:
            continue # empty tags are skipped

          if k not in tags_new:
            keys_untag.append(k)

        if not keys_dotag and not keys_untag:
          continue

        # if any of them set:
        instance_obj = ec2_resource.Instance(instance_id)
        instance_arn = 'arn:aws:ec2:%s:%s:instance/%s'%(instance_obj.placement['AvailabilityZone'][:-1], account_id, instance_id)

        if keys_dotag:
          logger.debug("[%s] Will tag %s with %s"%(runType_prefix, instance_id, json.dumps(keys_dotag)))
          if not dryRun:
            response = tagging_client.tag_resources(
              ResourceARNList=[instance_arn],
              Tags=keys_dotag
            )


        if keys_untag:
          logger.debug("[%s] Will untag %s with %s"%(runType_prefix, instance_id, json.dumps(keys_untag)))
          if not dryRun:
            response = tagging_client.untag_resources(
              ResourceARNList=[instance_arn],
              TagKeys=keys_untag
            )

    if dryRun:
      from termcolor import colored
      logger.info(colored("This was a dry run. Execute the same command again with `--not-dry-run` for actual tags push to aws ec2", "red"))
