# redshift pricing as of 2019-11-12 in USD per hour, on-demand, ohio
# https://aws.amazon.com/redshift/pricing/
redshiftPricing_dict = {
  'dc2.large': 0.25,
  'dc2.8xlarge': 4.80,
  'ds2.xlarge': 0.85,
  'ds2.8xlarge': 6.80,
  'dc1.large': 0.25,
  'dc1.8xlarge': 4.80,
}


# convert above dict to pandas dataframe
import pandas as pd
redshiftPricing_df = [{'NodeType': k, 'Cost': v} for k, v in redshiftPricing_dict.items()]
redshiftPricing_df = pd.DataFrame(redshiftPricing_df)
#print("redshift pricing")
#print(redshiftPricing_df)
