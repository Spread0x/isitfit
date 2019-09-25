"""
Manager class for getting datadog data for isitfit

Pre-requisites
    pip3 install datadog asciiplotlib pandas
    apt-get install gnuplot

set env vars
    export DATADOG_API_KEY=...
    export DATADOG_APP_KEY=...
    
Run tests
    pip3 install pytest
    pytest datadogManager.py
"""

import json
import time
import pandas as pd
import os

import logging
logger = logging.getLogger('isitfit')

# Configure the module according to your needs
from datadog import initialize

# Use Datadog REST API client
from datadog import api

SECONDS_IN_ONE_DAY = 60*60*24

class HostNotFoundInDdg(ValueError):
  pass

class DataNotFoundForHostInDdg(ValueError):
  pass

class DatadogAssistant:
    def __init__(self, start, end, host_id):
        self.end = end
        self.start = start
        self.host_id = host_id

    def _get_metrics_core(self, query, col_i):
        m = api.Metric.query(start=self.start, end=self.end, query=query, host=self.host_id)
        if len(m['series'])==0:
            raise DataNotFoundForHostInDdg("No %s found for %s"%(col_i, self.host_id))
        df = pd.DataFrame(m['series'][0]['pointlist'], columns=['ts_int', col_i])
        #import pdb
        #pdb.set_trace()
        df['ts_dt'] = pd.to_datetime(df.ts_int, origin='unix', unit='ms')
        return df
        
    def _get_meta(self):
        h_all = api.Hosts.search(host=self.host_id)
        if len(h_all['host_list'])==0:
            raise HostNotFoundInDdg("Did not find host %s in datadog"%self.host_id)

        h_i = h_all['host_list'][0]
        gohai = json.loads(h_i['meta']['gohai'])
        memory_total = int(gohai['memory']['total'].replace('kB',''))*1024
        out = {'cpuCores': h_i['meta']['cpuCores'], 'memory_total': memory_total}
        return out
        
    def get_metrics_cpu_max(self):
        # query language
        # https://docs.datadoghq.com/graphing/functions/
        # Use minimum so that cpu_used will be the maximum
        query = 'system.cpu.idle{host:%s}.rollup(min,%i)'%(self.host_id, SECONDS_IN_ONE_DAY)
        col_i = 'cpu_idle_min'
        df = self._get_metrics_core(query, col_i)
        # calculate cpu used as 100 - cpu_idle
        df['cpu_used_max'] = 100 - df.cpu_idle_min
        df['cpu_used_max'] = df['cpu_used_max'].astype(int)
        return df
        
    def get_metrics_cpu_avg(self):
        # repeat for average
        query = 'system.cpu.idle{host:%s}.rollup(avg,%i)'%(self.host_id, SECONDS_IN_ONE_DAY)
        col_i = 'cpu_idle_avg'
        df = self._get_metrics_core(query, col_i)
        df['cpu_used_avg'] = 100 - df.cpu_idle_avg
        df['cpu_used_avg'] = df['cpu_used_avg'].astype(int)
        return df

    def get_metrics_ram_max(self):
        # query language, check note above in get_metrics_cpu
        query = 'system.mem.free{host:%s}.rollup(min,%i)'%(self.host_id, SECONDS_IN_ONE_DAY)
        col_i = 'ram_free_min'
        df =  self._get_metrics_core(query, col_i)
        memory_total = self._get_meta()['memory_total']
        df['ram_free_min'] = df.ram_free_min / memory_total * 100
        df['ram_free_min'] = df['ram_free_min'].astype(int)
        df['ram_used_max'] = 100 - df['ram_free_min']
        return df

    def get_metrics_ram_avg(self):
        # query language, check note above in get_metrics_cpu
        query = 'system.mem.free{host:%s}.rollup(avg,%i)'%(self.host_id, SECONDS_IN_ONE_DAY)
        col_i = 'ram_free_avg'
        df =  self._get_metrics_core(query, col_i)
        memory_total = self._get_meta()['memory_total']
        df['ram_free_avg'] = df.ram_free_avg / memory_total * 100
        df['ram_free_avg'] = df['ram_free_avg'].astype(int)
        df['ram_used_avg'] = 100 - df['ram_free_avg']
        return df

class DatadogManager:
    
    def __init__(self):
        initialize()
        self.end = int(time.time())
        
        # datadog will automatically set the resolution based on the start-end range
        # if the ".rollup" is not used in the query
        # number of seconds in 1 hour, if no ".rollup" specified in query, this yields 20-second frequency from datadog
        # n_secs = 60*60
        # number of seconds in 90 days, if no ".rollup" specified in query, yields bi-daily from datadog
        n_secs = SECONDS_IN_ONE_DAY*90
        self.start = self.end - n_secs


    def is_configured(self):
      if os.getenv('DATADOG_API_KEY', None) is not None:
        if os.getenv('DATADOG_APP_KEY', None) is not None:
          return True
          
      return False


    def get_metrics_all(self, host_id):
        # FIXME: we already have cpu from cloudwatch, so maybe just focus on ram from datadog
        logger.debug("Fetching datadog data for %s"%host_id)
        ddgL2 = DatadogAssistant(self.start, self.end, host_id)
        df_cpu_max = ddgL2.get_metrics_cpu_max()
        df_cpu_avg = ddgL2.get_metrics_cpu_avg()
        df_ram_max = ddgL2.get_metrics_ram_max()
        df_ram_avg = ddgL2.get_metrics_ram_avg()
        df_all = (
            df_cpu_max
            .merge(df_cpu_avg, how='outer', on=['ts_int', 'ts_dt'])
            .merge(df_ram_max, how='outer', on=['ts_int', 'ts_dt'])
            .merge(df_ram_avg, how='outer', on=['ts_int', 'ts_dt'])
        )
        df_all = df_all[['ts_dt', 'cpu_used_max', 'cpu_used_avg', 'ram_used_max', 'ram_used_avg']]
        return df_all
