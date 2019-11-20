import logging
logger = logging.getLogger('isitfit')

from isitfit.utils import mergeSeriesOnTimestampRange
import numpy as np


class Ec2Common:
    def _handle_ec2obj(self, context_ec2):
        # parse out
        ec2_obj = context_ec2['ec2_obj']

        # logger.debug("%s, %s"%(ec2_obj.instance_id, ec2_obj.instance_type))

        # pandas series of CPU utilization, daily max, for 90 days
        df_metrics = context_ec2['df_metrics']

        # pandas series of number of cpu's available on the machine over time, past 90 days
        df_type_ts1 = context_ec2['df_type_ts1']
        df_type_ts1 = df_type_ts1.rename(columns={'ResourceSize1': 'instanceType'})

        # this is redundant with the implementation in _cloudwatch_metrics_core,
        # and it's here just in case the cached redis version is not a date,
        # but it's not really worth it to make a full refresh of the cache for this
        # if df_metrics.Timestamp.dtype==dt.date:
        try:
          df_metrics['Timestamp'] = df_metrics.Timestamp.dt.date
        except AttributeError:
          pass

        # convert type timeseries to the same timeframes as pcpu and n5mn
        #if ec2_obj.instance_id=='i-069a7808addd143c7':
        ec2_df = mergeSeriesOnTimestampRange(df_metrics, df_type_ts1, ['instanceType'])
        #logger.debug("\nafter merge series on timestamp range")
        #logger.debug(ec2_df.head())

        # merge with type changes (can't use .merge on timestamps, need to use .concat)
        #ec2_df = df_metrics.merge(df_type_ts2, left_on='Timestamp', right_on='EventTime', how='left')
        # ec2_df = pd.concat([df_metrics, df_type_ts2], axis=1)

        # merge with catalog
        ec2_df = ec2_df.merge(context_ec2['df_cat'][['API Name', 'cost_hourly']], left_on='instanceType', right_on='API Name', how='left')
        #logger.debug("\nafter merge with catalog")
        #logger.debug(ec2_df.head())

        # calculate number of running hours
        # In the latest 90 days, sampling is per minute in cloudwatch
        # https://aws.amazon.com/cloudwatch/faqs/
        # Q: What is the minimum resolution for the data that Amazon CloudWatch receives and aggregates?
        # A: ... For example, if you request for 1-minute data for a day from 10 days ago, you will receive the 1440 data points ...
        ec2_df['nhours'] = np.ceil(ec2_df.SampleCount/60)

        # set in context
        context_ec2['ec2_df'] = ec2_df

        # done
        return context_ec2


    def after_all(self, context_all):
        # unpack
        ec2_noCloudwatch, ec2_noCloudtrail = context_all['ec2_noCloudwatch'], context_all['ec2_noCloudtrail']


        # get now + 10 minutes
        # http://stackoverflow.com/questions/6205442/ddg#6205529
        import datetime as dt
        dt_now = dt.datetime.now()
        TRY_IN = 10
        now_plus_10 = dt_now + dt.timedelta(minutes = TRY_IN)
        now_plus_10 = now_plus_10.strftime("%H:%M")

        if len(ec2_noCloudwatch)>0:
          n_no_cw = len(ec2_noCloudwatch)
          has_more_cw = "..." if n_no_cw>5 else ""
          l_no_cw = ", ".join(ec2_noCloudwatch[:5])
          logger.warning("No cloudwatch data for %i resources: %s%s"%(n_no_cw, l_no_cw, has_more_cw))
          logger.warning("Try again in %i minutes (at %s) to check for new data"%(TRY_IN, now_plus_10))
          logger.info("")

        if len(ec2_noCloudtrail)>0:
          n_no_ct = len(ec2_noCloudtrail)
          has_more_ct = "..." if n_no_ct>5 else ""
          l_no_ct = ", ".join(ec2_noCloudtrail[:5])
          logger.warning("No cloudtrail data for %i resources: %s%s"%(n_no_ct, l_no_ct, has_more_ct))
          logger.warning("Try again in %i minutes (at %s) to check for new data"%(TRY_IN, now_plus_10))
          logger.info("")

        return context_all
