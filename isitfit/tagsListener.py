import logging
logger = logging.getLogger('isitfit')

class TagsListener:

  def __init__(self):
    # boto3 ec2 and cloudwatch data
    import boto3
    self.ec2_resource = boto3.resource('ec2')
    self.tags_list = []

  def fetch(self):
    logger.info("Counting EC2 instances")
    n_ec2_total = len(list(self.ec2_resource.instances.all()))
    logger.warning("Found a total of %i EC2 instances"%n_ec2_total)
    if n_ec2_total==0:
      return

    self.tags_list = []
    from tqdm import tqdm
    desc = "Scanning EC2 instances"
    ec2_all = self.ec2_resource.instances.all()
    for ec2_obj in tqdm(ec2_all, total=n_ec2_total, desc=desc, initial=1):
      tags_dict = {x['Key']: x['Value'] for x in ec2_obj.tags}
      tags_dict['instance_id'] = ec2_obj.instance_id
      self.tags_list.append(tags_dict)

  def dump(self):
    import tempfile
    import pandas as pd

    # https://pypi.org/project/termcolor/
    from termcolor import colored

    with tempfile.NamedTemporaryFile(prefix='isitfit-tags-', suffix='.csv', delete=False) as fh:
      logger.info("Converting tags list into dataframe")
      df = pd.DataFrame(self.tags_list)
      df = df.rename(columns={'instance_id': '_0_instance_id', 'Name': '_1_Name'}) # trick to keep instance ID and name as the first columns
      df = df.sort_index(axis=1)  # sort columns
      df = df.rename(columns={'_0_instance_id': 'instance_id', '_1_Name': 'Name'}) # undo trick

      logger.info(colored("Dumping data into %s"%fh.name, "cyan"))
      df.to_csv(fh.name, index=False)

      logger.info(colored("Done","cyan"))
      logger.info(colored("Consider `pip3 install visidata` and then `vd %s` for further filtering or exploration."%fh.name,"cyan"))
      logger.info(colored("More details about visidata at http://visidata.org/","cyan"))
