import logging
logger = logging.getLogger('isitfit')

import pandas as pd
from tabulate import tabulate

# https://pypi.org/project/termcolor/
from termcolor import colored

from isitfit.cost.redshift.reporter import ReporterBase




class ReporterOptimizeEc2(ReporterBase):

  def __init__(self):
    # for final csv file
    self.csv_fn_final = None

    # members that will contain the results of the optimization
    self.df_sort = None
    self.sum_val = None


  def postprocess(self, context_all):
    # unpack
    self.analyzer = context_all['analyzer']
    self.df_cat = context_all['df_cat']

    # process
    self._after_all()
    self._storecsv_all()

    # save to context for aggregator
    context_all['df_sort'] = self.df_sort
    context_all['sum_val'] = self.sum_val
    context_all['csv_fn_final'] = self.csv_fn_final

    # done
    return context_all


  def _after_all(self):
    df_all = pd.DataFrame(self.analyzer.ec2_classes)

    # if no data
    if df_all.shape[0]==0:
      self.df_sort = None
      self.sum_val = None
      return

    # merge current type hourly cost
    map_cost = self.df_cat[['API Name', 'cost_hourly']]
    df_all = df_all.merge(map_cost, left_on='instance_type', right_on='API Name', how='left').drop(['API Name'], axis=1)

    # merge the next-smaller instance type from the catalog for instances classified as Underused
    map_smaller = self.df_cat[['API Name', 'type_smaller', 'Linux On Demand cost_smaller']].rename(columns={'Linux On Demand cost_smaller': 'cost_hourly_smaller'})
    df_all = df_all.merge(map_smaller, left_on='instance_type', right_on='API Name', how='left').drop(['API Name'], axis=1)

    # merge next-larger instance type
    map_larger = self.df_cat[['API Name', 'type_smaller', 'cost_hourly']].rename(columns={'type_smaller': 'API Name', 'API Name': 'type_larger', 'cost_hourly': 'cost_hourly_larger'})
    df_all = df_all.merge(map_larger, left_on='instance_type', right_on='API Name', how='left').drop(['API Name'], axis=1)

    # convert from hourly to 3-months
    for fx1, fx2 in [('cost_3m', 'cost_hourly'), ('cost_3m_smaller', 'cost_hourly_smaller'), ('cost_3m_larger', 'cost_hourly_larger')]:
      df_all[fx1] = df_all[fx2] * 24 * 30 * 3
      df_all[fx1] = df_all[fx1].fillna(value=0).astype(int)

    # imply a recommended type
    from isitfit.cost.ec2.calculator_optimize import class2recommendedCore
    df_rec = df_all.apply(class2recommendedCore, axis=1).apply(pd.Series)
    df_all['recommended_type'], df_all['savings'] = df_rec['recommended_type'], df_rec['savings']
    df_all['savings'] = df_all.savings.fillna(value=0).astype(int)

    # keep a subset of columns
    df_all = df_all[['region', 'instance_id', 'instance_type', 'classification_1', 'classification_2', 'cost_3m', 'recommended_type', 'savings', 'tags']]

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


  def _storecsv_all(self, *args, **kwargs):
      if self.df_sort is None:
        return

      import tempfile
      with tempfile.NamedTemporaryFile(prefix='isitfit-full-ec2-', suffix='.csv', delete=False) as  csv_fh_final:
        self.csv_fn_final = csv_fh_final.name
        logger.debug(colored("Saving final results to %s"%csv_fh_final.name, "cyan"))
        self.df_sort.to_csv(csv_fh_final.name, index=False)
        logger.debug(colored("Save complete", "cyan"))


  def display(self, context_all):
    if self.df_sort is None:
      logger.info(colored("No EC2 instances found", "red"))
      return context_all

    # display
    # Edit 2019-09-25 just show the full list. Will add filtering later. This way it's less ambiguous when all instances are "Normal"
    # self.df_sort.dropna(subset=['recommended_type'], inplace=True)
    
    # if no recommendations
    if self.df_sort.shape[0]==0:
      logger.info(colored("No optimizations from isitfit for this AWS EC2 account", "red"))
      return context_all
    
    # if there are recommendations, show them
    sum_comment = "extra cost" if self.sum_val>0 else "savings"
    sum_color = "red" if self.sum_val>0 else "green"

    #logger.info("Optimization based on the following CPU thresholds:")
    #logger.info(self.thresholds)
    #logger.info("")
    logger.info(colored("Recommended %s: %0.0f $ (over the next 3 months)"%(sum_comment, self.sum_val), sum_color))
    logger.info("")

    # display dataframe
    from isitfit.utils import display_df
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

    if self.analyzer.n!=-1:
      logger.info(colored("This table has been filtered for only the 1st %i underused results"%self.analyzer.n, "cyan"))

    return context_all
