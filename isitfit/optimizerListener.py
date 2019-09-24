import logging
logger = logging.getLogger('isitfit')

import pandas as pd
from tabulate import tabulate

# https://pypi.org/project/termcolor/
from termcolor import colored


def df2tabulate(df):
  return tabulate(df.set_index('instance_id'), headers='keys', tablefmt='psql')


def class2recommendedType(r):
  if r.classification_1 == 'Underused':
    # FIXME classification 2 will contain if it's a burstable workload or lambda-convertible
    # that would mean that the instance is downsizable twice, so maybe need to return r.type_smaller2x
    return r.type_smaller

  if r.classification_1=='Overused':
    return r.type_larger

  return None


def class2recommendedCost(r):
  if r.classification_1 == 'Underused':
    # FIXME add savings from the twice downsizing in class2recommendedType if it's a burstable workload or lambda-convertible,
    # then calculate the cost from lambda functions and add it as overhead here
    return r.cost_3m_smaller-r.cost_3m

  if r.classification_1=='Overused':
    return r.cost_3m_larger-r.cost_3m

  return None


class OptimizerListener:

  def __init__(self, n, thresholds = None):
    self.n = n

    if thresholds is None:
      thresholds = {
        'rightsize': {'idle': 3, 'low': 30, 'high': 70},
        'burst': {'low': 20, 'high': 80}
      }

    # iterate over all ec2 instances
    self.thresholds = thresholds
    self.ec2_classes = []


  def _ec2df_to_classification(self, ec2_df):
    maxmax = ec2_df.Maximum.max()
    maxavg = ec2_df.Average.max()
    avgmax = ec2_df.Maximum.mean()
    #print("ec2_df.{maxmax,avgmax,maxavg} = ", maxmax, avgmax, maxavg)

    # check if good to convert to burstable or lambda
    # i.e. daily data shows few large spikes
    thres = self.thresholds['burst']
    if maxmax >= thres['high'] and avgmax <= thres['low'] and maxavg <= thres['low']:
      return 'Underused', 'Burstable, daily resolution'

    # check rightsizing
    # i.e. no special spikes in daily data
    # FIXME: can check hourly data for higher precision here
    thres = self.thresholds['rightsize']
    if maxmax <= thres['idle']:
      return 'Idle', None
    elif maxmax <= thres['low']:
      return 'Underused', None
    elif maxmax >= thres['high'] and avgmax >= thres['high'] and maxavg >= thres['high']:
      return 'Overused', None
    elif maxmax >= thres['high'] and avgmax >= thres['high'] and maxavg <= thres['low']:
      return 'Underused', 'Burstable, hourly resolution'

    return 'Normal', None


  def per_ec2(self, ec2_obj, ec2_df, mm):
    #print(ec2_obj.instance_id)
    ec2_c1, ec2_c2 = self._ec2df_to_classification(ec2_df)

    self.ec2_classes.append({
      'instance_id': ec2_obj.instance_id,
      'instance_type': ec2_obj.instance_type,
      'classification_1': ec2_c1,
      'classification_2': ec2_c2
    })

    if self.n!=0:
      sub_underused = [x for x in self.ec2_classes if x['classification_1']=='Underused']
      if len(sub_underused) >= self.n:
        # break early
        self.after_all(None, mm)
        import sys
        sys.exit(0)




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

    # convert from hourly to 3-months
    for fx1, fx2 in [('cost_3m', 'cost_hourly'), ('cost_3m_smaller', 'cost_hourly_smaller'), ('cost_3m_larger', 'cost_hourly_larger')]:
      df_all[fx1] = df_all[fx2] * 24 * 30 * 3
      df_all[fx1] = df_all[fx1].fillna(value=0).astype(int)

    # imply a recommended type
    df_all['recommended_type'] = df_all.apply(class2recommendedType, axis=1)
    df_all['savings'] = df_all.apply(class2recommendedCost, axis=1)
    df_all['savings'] = df_all.savings.fillna(value=0).astype(int)
    df_all = df_all[['instance_id', 'instance_type', 'classification_1', 'classification_2', 'cost_3m', 'recommended_type', 'savings']]

    # display
    #df_all = df_all.set_index('classification_1')
    #for v in ['Idle', 'Underused', 'Overused', 'Normal']:
    #  logger.info("\nInstance classification_1: %s"%v)
    #  if v not in df_all.index:
    #    logger.info("None")
    #  else:
    #    logger.info(df_all.loc[[v]]) # use double brackets to maintain single-row dataframes https://stackoverflow.com/a/45990057/4126114
    #
    #  logger.info("\n")

    # display
    df_sort = df_all.sort_values(['savings'], ascending=True)
    df_sort.dropna(subset=['recommended_type'], inplace=True)
    
    # if no recommendations
    if df_sort.shape[0]==0:
      logger.info(colored("No optimizations from isitfit for this AWS EC2 account", "red"))
      return
    
    # if there are recommendations, show them
    sum_val = df_all.savings.sum()
    sum_comment = "extra cost" if sum_val>0 else "savings"
    sum_color = "red" if sum_val>0 else "green"

    #logger.info("Optimization based on the following CPU thresholds:")
    #logger.info(self.thresholds)
    #logger.info("")
    logger.info(colored("Recommended %s: %0.0f $ (over the next 3 months)"%(sum_comment, sum_val), sum_color))

    if self.n!=0:
      logger.info(colored("This table has been filtered for only the 1st %i scan results"%self.n, "cyan"))

    logger.info("")
    logger.info("")

    with pd.option_context("display.max_columns", 10):
      if df_sort.shape[0]<=10:
        logger.info("Details")
        logger.info(df2tabulate(df_sort))
      else:
        logger.info("Top savings (down-sizable):")
        logger.info(df2tabulate(df_sort.head(n=5)))
        logger.info("Bottom savings (up-sizable):")
        logger.info(df2tabulate(df_sort.tail(n=5)))

