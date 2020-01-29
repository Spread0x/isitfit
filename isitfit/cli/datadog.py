from .. import isitfit_version
import click

from isitfit.cli.click_descendents import IsitfitCommand, isitfit_group, isitfit_option_base, isitfit_option_profile


@isitfit_group(help="Datadog utilities", invoke_without_command=False, hidden=False)
@click.pass_context
def datadog(ctx):
  # FIXME click bug: `isitfit command subcommand --help` is calling the code in here. Workaround is to check --help and skip the whole section
  import sys
  if '--help' in sys.argv: return

  # usage stats
  from isitfit.utils import ping_matomo
  ping_matomo("/datadog")

  # manager of redis-pandas caching
  from isitfit.cost.cacheManager import RedisPandas as RedisPandasCacheManager
  cache_man = RedisPandasCacheManager()

  from isitfit.cost.metrics_datadog import DatadogCached
  ctx.obj['ddg'] = DatadogCached(cache_man)


import datadog as datadog_api


@datadog.command(help="Dump raw data from datadog for a day of an EC2 ID", cls=IsitfitCommand)
@click.argument('date', type=click.DateTime(formats=["%Y-%m-%d"]))
@click.argument('aws_id')
@click.pass_context
def dump(ctx, date, aws_id):
  # usage stats
  from isitfit.utils import ping_matomo
  ping_matomo("/datadog/dump")

  ddgL1 = ctx.obj['ddg']

  # get as dataframe, daily
  df = ddgL1.get_metrics_all(aws_id)
  # drop nhours column since useless here
  del df['nhours']
  print("Daily usage")
  print(df)
  print("")

  # convert aws ID to datadog hostname
  dd_hostname = ddgL1.map_aws_dd[aws_id]

  # higher freq
  # query language, check note above in get_metrics_cpu
  SECONDS_PER_POINT = 60*10 # 60*60 # *24

  import datetime as dt
  date_str = date.strftime("%Y-%m-%d")
  dt_start="%s 00:00:00"%date_str
  dt_end="%s 23:59:59"%date_str
  dt_start = dt.datetime.strptime(dt_start, "%Y-%m-%d %H:%M:%S")
  dt_end = dt.datetime.strptime(dt_end, "%Y-%m-%d %H:%M:%S")
  import time
  conv2sec = lambda x: time.mktime(x.timetuple())
  ue_start = conv2sec(dt_start)
  ue_end   = conv2sec(dt_end)

  # query datadog, result as json
  # https://docs.datadoghq.com/api/?lang=python#query-timeseries-points
  #datadog_api.initialize()
  #m = datadog_api.api.Metric.query(start=ue_start, end=ue_end, query=query)
  #print(m)

  # repeat as dataframe
  from isitfit.cost.metrics_datadog import DatadogApiWrap
  apiwrap = DatadogApiWrap()
  df_all = []
  metric_all = [
    ('system.cpu.idle', 'cpu_idle_min', 'system.cpu.idle{host:%s}.rollup(min,%i)'),
    ('system.mem.free', 'mem_free_min', 'system.mem.free{host:%s}.rollup(min,%i)'),
    ('system.cpu.idle', 'cpu_idle_max', 'system.cpu.idle{host:%s}.rollup(max,%i)'),
    ('system.mem.free', 'mem_free_max', 'system.mem.free{host:%s}.rollup(max,%i)')
  ]
  for metric_name, col_name, query_t in metric_all:
    query_v = query_t%(dd_hostname, SECONDS_PER_POINT)
    df_i = apiwrap.metric_query(
      dd_hostname=dd_hostname,
      start=ue_start,
      end=ue_end,
      query=query_v,
      metric_name=metric_name,
      dfcol_name=col_name
    )
    df_i.set_index('ts_dt', inplace=True)
    df_all.append(df_i)

  # concat all
  import pandas as pd
  df_all = pd.concat(df_all, axis=1)
  pd.set_option("display.max_rows", None)
  print("Datadog details")
  print(df_all)

#  memory_total = ddgL1._get_meta()['memory_total']
#  df['ram_free_min'] = df.ram_free_min / memory_total * 100
#  df['ram_free_min'] = df['ram_free_min'].astype(int)
#  df['ram_used_max'] = 100 - df['ram_free_min']
#  return df


