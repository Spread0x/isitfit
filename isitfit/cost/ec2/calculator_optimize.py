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


#---------------------------


def class2recommendedCore(r):
  o = { 'recommended_type': None,
        'savings': None
      }

  if r.classification_1=='Underused':
    # FIXME classification 2 will contain if it's a burstable workload or lambda-convertible
    # that would mean that the instance is downsizable twice, so maybe need to return r.type_smaller2x
    # FIXME add savings from the twice downsizing in class2recommendedType if it's a burstable workload or lambda-convertible,
    # then calculate the cost from lambda functions and add it as overhead here
    o = { 'recommended_type': r.type_smaller,
          'savings': r.cost_3m_smaller-r.cost_3m
        }

  if r.classification_1=='Idle':
    # Maybe idle servers should be recommended to "stop"
    o = { 'recommended_type': r.type_smaller,
          'savings': r.cost_3m_smaller-r.cost_3m
        }

  if r.classification_1=='Overused':
    # This is costing more
    o = {'recommended_type': r.type_larger,
         'savings': r.cost_3m_larger-r.cost_3m
        }

  return o

#---------------------------------


def ec2obj_to_name(ec2_obj):
    if ec2_obj.tags is None:
      return None

    ec2_name = [x for x in ec2_obj.tags if x['Key']=='Name']
    if len(ec2_name)==0:
      return None

    return ec2_name[0]['Value']


class CalculatorOptimizeEc2:

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

    # for csv streaming
    self.csv_fn_intermediate = None
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


  def handle_pre(self, context_pre):
      # a csv file handle to which to stream results
      self.csv_fn_intermediate = tempfile.NamedTemporaryFile(prefix='isitfit-intermediate-', suffix='.csv', delete=False)
      logger.info(colored("Intermediate results will be streamed to %s"%self.csv_fn_intermediate.name, "cyan"))
      self.csv_fh = open(self.csv_fn_intermediate.name, 'w')
      self.csv_writer = csv.writer(self.csv_fh)

      # done
      return context_pre


  def per_ec2(self, context_ec2):
    # parse out context keys
    ec2_obj, ec2_df, mm, ddg_df = context_ec2['ec2_obj'], context_ec2['ec2_df'], context_ec2['mainManager'], context_ec2['ddg_df']

    #print(ec2_obj.instance_id)
    ec2_c1, ec2_c2 = self._ec2df_to_classification(ec2_df, ddg_df)

    ec2_name = ec2obj_to_name(ec2_obj)

    taglist = ec2_obj.tags

    # Reported in github issue 8: NoneType object is not iterable
    # https://github.com/autofitcloud/isitfit/issues/8
    if taglist is None:
      taglist = []

    if context_ec2['filter_tags'] is not None:
      # filter the tag list for only those containing the filter-tags string
      f_tn = context_ec2['filter_tags'].lower()
      # similar to the isitfit.mainManager.tagsContain function, but filtering the tags themselves
      taglist = [x for x in taglist if (f_tn in x['Key'].lower()) or (f_tn in x['Value'].lower())]

    taglist = ["%s = %s"%(x['Key'], x['Value']) for x in taglist]
    taglist = "\n".join(taglist)

    ec2_res = OrderedDict()
    ec2_res['region'] = ec2_obj.region_name
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
    if self.n!=-1:
      sub_underused = [x for x in self.ec2_classes if x['classification_1']=='Underused']
      if len(sub_underused) >= self.n:
        # break early
        context_ec2['break_iterator'] = True

    # done
    return context_ec2


