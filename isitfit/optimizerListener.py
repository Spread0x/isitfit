import logging
logger = logging.getLogger('isitfit')

import pandas as pd

# https://pypi.org/project/termcolor/
from termcolor import colored


class OptimizerListener:

  def __init__(self, thresholds = None):
    if thresholds is None:
      thresholds = {'idle': 3, 'low': 30, 'high': 70}

    # iterate over all ec2 instances
    self.thresholds = thresholds
    self.ec2_classes = []


  def per_ec2(self, ec2_obj, ec2_df):
    maxmax = ec2_df.Maximum.max()
    ec2_c = 'Unknown'
    if maxmax <= self.thresholds['idle']:
      ec2_c = 'Idle'
    elif maxmax <= self.thresholds['low']:
      ec2_c = 'Underused'
    elif maxmax >= self.thresholds['high']:
      ec2_c = 'Overused'
    else:
      ec2_c = 'Normal'

    self.ec2_classes.append({
      'instance_id': ec2_obj.instance_id,
      'instance_type': ec2_obj.instance_type,
      'max_cpu': maxmax,
      'classification': ec2_c
    })



  def after_all(self, n_ec2, mm):
    df_all = pd.DataFrame(self.ec2_classes)
    df_all['max_cpu'] = df_all.max_cpu.astype('int')

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
    class2recommendedType = lambda r: r.type_smaller if r.classification=='Underused' else (r.type_larger if r.classification=='Overused' else None)
    class2recommendedCost = lambda r: r.cost_hourly_smaller-r.cost_hourly if r.classification=='Underused' else (r.cost_hourly_larger-r.cost_hourly if r.classification=='Overused' else None)
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

    logger.info("Optimization based on the following CPU thresholds:")
    logger.info(self.thresholds)
    logger.info("")
    logger.info(colored("Recommendation value: %f $/hour"%sum_val, sum_color))
    logger.info("i.e. if you implement these recommendations, this is %s"%colored(sum_comment, sum_color))
    logger.info("")
    logger.info("")

    if df_sort.shape[0]<=10:
      logger.info("Details")
      logger.info(df_sort)
    else:
      logger.info("Top savings (down-sizable):")
      logger.info(df_sort.head(n=5))
      logger.info("Bottom savings (up-sizable):")
      logger.info(df_sort.tail(n=5))

