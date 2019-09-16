import logging
logger = logging.getLogger('isitfit')

import pandas as pd

# https://pypi.org/project/termcolor/
from termcolor import colored


def class2recommendedType(r):
  if r.classification in ['Underused', 'Lambda']:
    # FIXME lambda-convertible would mean that the instance is downsizable twice, so maybe need to return r.type_smaller2x
    return r.type_smaller

  if r.classification=='Overused':
    return r.type_larger

  return None


def class2recommendedCost(r):
  if r.classification in ['Underused', 'Lambda']:
    # FIXME add savings from the twice downsizing in class2recommendedType, then calculate the cost from lambda functions and add it as overhead here
    return r.cost_hourly_smaller-r.cost_hourly

  if r.classification=='Overused':
    return r.cost_hourly_larger-r.cost_hourly

  return None


class OptimizerListener:

  def __init__(self, thresholds = None):
    if thresholds is None:
      thresholds = {
        'rightsize': {'idle': 3, 'low': 30, 'high': 70},
        'lambda': {'low': 20, 'high': 80}
      }

    # iterate over all ec2 instances
    self.thresholds = thresholds
    self.ec2_classes = []


  def _ec2df_to_classification(self, ec2_df):
    maxmax = ec2_df.Maximum.max()
    maxavg = ec2_df.Average.max()
    #print("ec2_df.maxmax, maxavg=", maxmax, maxavg)

    # check if good to convert to lambda
    thres = self.thresholds['lambda']
    if maxmax >= thres['high'] and maxavg <= thres['low']:
      return 'Lambda'

    # check rightsizing
    thres = self.thresholds['rightsize']
    if maxmax <= thres['idle']:
      return 'Idle'
    elif maxmax <= thres['low']:
      return 'Underused'
    elif maxmax >= thres['high']:
      return 'Overused'

    return 'Normal'


  def per_ec2(self, ec2_obj, ec2_df):
    #print(ec2_obj.instance_id)
    ec2_c = self._ec2df_to_classification(ec2_df)

    self.ec2_classes.append({
      'instance_id': ec2_obj.instance_id,
      'instance_type': ec2_obj.instance_type,
      'classification': ec2_c
    })



  def after_all(self, n_ec2, mm):
    df_all = pd.DataFrame(self.ec2_classes)

    # merge current type hourly cost
    map_cost = mm.df_cat[['API Name', 'cost_hourly']]
    df_all = df_all.merge(map_cost, left_on='instance_type', right_on='API Name', how='left').drop(['API Name'], axis=1)

    # merge the next-smaller instance type from the catalog for instances classified as Underused
    map_smaller = mm.df_cat[['API Name', 'type_smaller', 'Linux On Demand cost_smaller']].rename(columns={'Linux On Demand cost_smaller': 'cost_hourly_smaller'})
    df_all = df_all.merge(map_smaller, left_on='instance_type', right_on='API Name', how='left').drop(['API Name'], axis=1)

    # merge next-larger instance type
    map_larger = mm.df_cat[['API Name', 'type_smaller', 'cost_hourly']].rename(columns={'type_smaller': 'API Name', 'API Name': 'type_larger', 'cost_hourly': 'cost_hourly_larger'})
    df_all = df_all.merge(map_larger, left_on='instance_type', right_on='API Name', how='left').drop(['API Name'], axis=1)

    # imply a recommended type
    df_all['recommended_type'] = df_all.apply(class2recommendedType, axis=1)
    df_all['recommended_costdiff'] = df_all.apply(class2recommendedCost, axis=1)
    df_all = df_all.drop(['type_smaller', 'type_larger', 'cost_hourly_smaller', 'cost_hourly_larger'], axis=1)

    # display
    #df_all = df_all.set_index('classification')
    #for v in ['Idle', 'Underused', 'Overused', 'Normal']:
    #  logger.info("\nInstance classification: %s"%v)
    #  if v not in df_all.index:
    #    logger.info("None")
    #  else:
    #    logger.info(df_all.loc[[v]]) # use double brackets to maintain single-row dataframes https://stackoverflow.com/a/45990057/4126114
    #
    #  logger.info("\n")

    # display
    df_sort = df_all.sort_values(['recommended_costdiff'], ascending=True)
    df_sort.dropna(subset=['recommended_costdiff'], inplace=True)
    sum_val = df_all.recommended_costdiff.sum()
    sum_comment = "extra cost since positive" if sum_val>0 else "savings since negative"
    sum_color = "red" if sum_val>0 else "green"

    #logger.info("Optimization based on the following CPU thresholds:")
    #logger.info(self.thresholds)
    #logger.info("")
    logger.info(colored("Recommendation value: %f $/hour"%sum_val, sum_color))
    logger.info("i.e. if you implement these recommendations, this is %s"%colored(sum_comment, sum_color))
    logger.info("")
    logger.info("")

    with pd.option_context("display.max_columns", 10):
      if df_sort.shape[0]<=10:
        logger.info("Details")
        logger.info(df_sort)
      else:
        logger.info("Top savings (down-sizable):")
        logger.info(df_sort.head(n=5))
        logger.info("Bottom savings (up-sizable):")
        logger.info(df_sort.tail(n=5))

