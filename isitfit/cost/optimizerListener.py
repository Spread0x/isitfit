import logging
logger = logging.getLogger('isitfit')

import pandas as pd
from tabulate import tabulate
import tempfile
import csv
from collections import OrderedDict

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


def ec2obj_to_name(ec2_obj):
    if ec2_obj.tags is None:
      return None

    ec2_name = [x for x in ec2_obj.tags if x['Key']=='Name']
    if len(ec2_name)==0:
      return None

    return ec2_name[0]['Value']


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

    # members that will contain the results of the optimization
    self.df_sort = None
    self.sum_val = None

    # for csv streaming
    self.csv_fn_intermediate = None
    self.csv_fn_final = None
    self.csv_fh = None
    self.csv_writer = None

  
  def __exit__(self):
    self.csv_fh.close()


  def _xxx_to_classification(self, xxx_maxmax, xxx_maxavg, xxx_avgmax):
    # check if good to convert to burstable or lambda
    # i.e. daily data shows few large spikes
    thres = self.thresholds['burst']
    if xxx_maxmax >= thres['high'] and xxx_avgmax <= thres['low'] and xxx_maxavg <= thres['low']:
      return 'Underused', 'Burstable daily'

    # check rightsizing
    # i.e. no special spikes in daily data
    # FIXME: can check hourly data for higher precision here
    thres = self.thresholds['rightsize']
    if xxx_maxmax <= thres['idle']:
      return 'Idle', None
    elif xxx_maxmax <= thres['low']:
      return 'Underused', None
    elif xxx_maxmax >= thres['high'] and xxx_avgmax >= thres['high'] and xxx_maxavg >= thres['high']:
      return 'Overused', None
    elif xxx_maxmax >= thres['high'] and xxx_avgmax >= thres['high'] and xxx_maxavg <= thres['low']:
      return 'Underused', 'Burstable intraday'

    return 'Normal', None


  def _ec2df_to_classification(self, ec2_df, ddg_df):
    cpu_maxmax = ec2_df.Maximum.max()
    cpu_maxavg = ec2_df.Average.max()
    cpu_avgmax = ec2_df.Maximum.mean()
    cpu_c1, cpu_c2 = self._xxx_to_classification(cpu_maxmax, cpu_maxavg, cpu_avgmax)
    #print("ec2_df.{maxmax,avgmax,maxavg} = ", maxmax, avgmax, maxavg)

    if ddg_df is None:
      cpu_c2 = [cpu_c2, "No memory data"]
      cpu_c2 = [x for x in cpu_c2 if x is not None]
      cpu_c2 = ", ".join(cpu_c2)
      return cpu_c1, cpu_c2

    # continue with datadog data
    ram_maxmax = ddg_df.ram_used_max.max()
    ram_maxavg = ddg_df.ram_used_max.mean()
    ram_avgmax = ddg_df.ram_used_avg.max()
    ram_c1, ram_c2 = self._xxx_to_classification(ram_maxmax, ram_maxavg, ram_avgmax)

    # consolidate ram with cpu
    out_c2 = ["CPU + RAM checked",
              "CPU: %s"%cpu_c2 if cpu_c2 is not None else None,
              "RAM: %s"%ram_c2 if ram_c2 is not None else None ]
    out_c2 = ", ".join([x for x in out_c2 if x is not None])
    if cpu_c1=='Overused' or ram_c1=='Overused':
      return 'Overused', out_c2

    if cpu_c1=='Normal' or ram_c1=='Normal':
      return 'Normal', out_c2

    return 'Underused', out_c2


  def handle_pre(self):
      # a csv file handle to which to stream results
      self.csv_fn_intermediate = tempfile.NamedTemporaryFile(prefix='isitfit-intermediate-', suffix='.csv', delete=False)
      logger.info(colored("Intermediate results will be streamed to %s"%self.csv_fn_intermediate.name, "cyan"))
      self.csv_fh = open(self.csv_fn_intermediate.name, 'w')
      self.csv_writer = csv.writer(self.csv_fh)


  def per_ec2(self, ec2_obj, ec2_df, mm, ddg_df):
    #print(ec2_obj.instance_id)
    ec2_c1, ec2_c2 = self._ec2df_to_classification(ec2_df, ddg_df)

    ec2_name = ec2obj_to_name(ec2_obj)

    taglist = ec2_obj.tags

    # Reported in github issue 8: NoneType object is not iterable
    # https://github.com/autofitcloud/isitfit/issues/8
    if taglist is None:
      taglist = []

    if mm.filter_tags is not None:
      # filter the tag list for only those containing the filter-tags string
      f_tn = mm.filter_tags.lower()
      # similar to the isitfit.mainManager.tagsContain function, but filtering the tags themselves
      taglist = [x for x in taglist if (f_tn in x['Key'].lower()) or (f_tn in x['Value'].lower())]

    taglist = ["%s = %s"%(x['Key'], x['Value']) for x in taglist]
    taglist = "\n".join(taglist)

    ec2_res = OrderedDict()
    ec2_res['instance_id'] = ec2_obj.instance_id
    ec2_res['instance_type'] = ec2_obj.instance_type
    ec2_res['classification_1'] = ec2_c1
    ec2_res['classification_2'] = ec2_c2
    ec2_res['tags'] = taglist

    # write csv header
    if len(self.ec2_classes)==0:
      self.csv_writer.writerow(['name'] + [k for k,v in ec2_res.items() if k!='tags'])# save header

    # save intermediate result to csv file
    # Try to stick to 1 row per instance
    # Drop the tags because they're too much to include
    csv_row = [ec2_name] + [v.replace("\n", ";") for k,v in ec2_res.items() if k!='tags']
    self.csv_writer.writerow(csv_row)

    # gathering results
    self.ec2_classes.append(ec2_res)

    # check if should return early
    if self.n!=0:
      sub_underused = [x for x in self.ec2_classes if x['classification_1']=='Underused']
      if len(sub_underused) >= self.n:
        # break early
        self.after_all(None, mm, None)
        import sys
        sys.exit(0)


  def after_all(self, n_ec2_total, mm, n_ec2_all):
    df_all = pd.DataFrame(self.ec2_classes)

    # if no data
    if df_all.shape[0]==0:
      self.df_sort = None
      self.sum_val = None
      return

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

    # keep a subset of columns
    df_all = df_all[['instance_id', 'instance_type', 'classification_1', 'classification_2', 'cost_3m', 'recommended_type', 'savings', 'tags']]

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

    # main results
    self.df_sort = df_all.sort_values(['savings'], ascending=True)
    self.sum_val = df_all.savings.sum()


  def storecsv_all(self, *args, **kwargs):
      if self.df_sort is None:
        return

      with tempfile.NamedTemporaryFile(prefix='isitfit-full-ec2-', suffix='.csv', delete=False) as  csv_fh_final:
        self.csv_fn_final = csv_fh_final.name
        logger.debug(colored("Saving final results to %s"%csv_fh_final.name, "cyan"))
        self.df_sort.to_csv(csv_fh_final.name, index=False)
        logger.debug(colored("Save complete", "cyan"))


  def display_all(self, *args, **kwargs):
    if self.df_sort is None:
      logger.info(colored("No EC2 instances found", "red"))
      return

    # display
    # Edit 2019-09-25 just show the full list. Will add filtering later. This way it's less ambiguous when all instances are "Normal"
    # self.df_sort.dropna(subset=['recommended_type'], inplace=True)
    
    # if no recommendations
    if self.df_sort.shape[0]==0:
      logger.info(colored("No optimizations from isitfit for this AWS EC2 account", "red"))
      return
    
    # if there are recommendations, show them
    sum_comment = "extra cost" if self.sum_val>0 else "savings"
    sum_color = "red" if self.sum_val>0 else "green"

    #logger.info("Optimization based on the following CPU thresholds:")
    #logger.info(self.thresholds)
    #logger.info("")
    logger.info(colored("Recommended %s: %0.0f $ (over the next 3 months)"%(sum_comment, self.sum_val), sum_color))
    logger.info("")

    # display dataframe
    from ..utils import display_df
    display_df(
      "Recommended EC2 size changes",
      self.df_sort,
      self.csv_fn_final,
      self.df_sort.shape,
      logger
    )

#    with pd.option_context("display.max_columns", 10):
#      logger.info("Details")
#      if self.df_sort.shape[0]<=10:
#        logger.info(df2tabulate(self.df_sort))
#      else:
#        logger.info(df2tabulate(self.df_sort.head(n=5)))
#        logger.info("...")
#        logger.info(df2tabulate(self.df_sort.tail(n=5)))
#        logger.info("")
#        logger.info(colored("Table originally with %i rows is truncated for top and bottom 5 only."%self.df_sort.shape[0], "cyan"))
#        logger.info(colored("Consider filtering it with --n=x for the 1st x results or --filter-tags=foo using a value from your own EC2 tags.", "cyan"))

    if self.n!=0:
      logger.info(colored("This table has been filtered for only the 1st %i underused results"%self.n, "cyan"))

