# AWS_DEFAULT_REGION=us-east-2 python3 -m isitfit.cost.test_redshift
# Related
# https://docs.datadoghq.com/integrations/amazon_redshift/
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/redshift.html#Redshift.Paginator.DescribeClusters

import pandas as pd
from isitfit.cost.mainManager import NoCloudwatchException


# redshift pricing as of 2019-11-12 in USD per hour, on-demand, ohio
# https://aws.amazon.com/redshift/pricing/
from isitfit.cost.redshift_common import redshiftPricing_dict



class CalculatorBaseRedshift:


  def __init__(self):
    # define the list in the constructor because if I define it as a class member above,
    # then it gets reused between instantiations of derived classes
    self.analyze_list = []
    self.analyze_df = None


  def per_ec2(self, context_ec2):
      rc_describe_entry = context_ec2['ec2_dict']

      # for types not yet in pricing dictionary above
      rc_type = rc_describe_entry['NodeType']
      if rc_type not in redshiftPricing_dict.keys():
        raise NoCloudwatchException

      return context_ec2


  def after_all(self, context_all):
    # To be used by derived class *after* its own implementation

    # gather into a single dataframe
    self.analyze_df = pd.DataFrame(self.analyze_list)

    # update number of analyzed clusters
    context_all['n_rc_analysed'] = self.analyze_df.shape[0]

    # Edit 2019-11-20 no need to through exception here
    # This way, the code can proceed to show a report, and possibly proceed to other services than redshift
    #if context_all['n_rc_analysed']==0:
    #  from isitfit.utils import IsitfitCliError
    #  raise IsitfitCliError("No redshift clusters analyzed", context_all['click_ctx'])

    return context_all


  def calculate(self, context_all):
    raise Exception("To be implemented by derived class")





