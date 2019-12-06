from isitfit.cost.ec2_analyze import BinCapUsed
import datetime as dt
import pytest
import pandas as pd

@pytest.fixture
def FakeMm():
    class FakeMm:
      StartTime = dt.datetime(2019,1,15)
      EndTime = dt.datetime(2019,4,15)

    return FakeMm


class TestBinCapUsedHandlePre:
  def test_preNoBreak(self, FakeMm):
    bcs = BinCapUsed()
    ret = bcs.handle_pre({'mainManager': FakeMm()})
    assert ret is not None

  def test_3m(self, FakeMm):
    bcs = BinCapUsed()
    bcs.handle_pre({'mainManager': FakeMm()})

    e = pd.DataFrame([
        (dt.date(2019,1,31), 0, 0, 0, frozenset([])),
        (dt.date(2019,2,28), 0, 0, 0, frozenset([])),
        (dt.date(2019,3,31), 0, 0, 0, frozenset([])),
        (dt.date(2019,4,30), 0, 0, 0, frozenset([]))
      ],
      columns=['Timestamp', 'capacity_usd', 'used_usd', 'count_analyzed', 'regions_set']
    )
    e['Timestamp'] = pd.to_datetime(e['Timestamp'])
    e.set_index('Timestamp', inplace=True)

    pd.testing.assert_frame_equal(e, bcs.df_bins)


class TestBinCapUsedPerEc2:
  def test_1m(self, FakeMm):
    # prepare input
    df1 = pd.DataFrame([
          (dt.date(2019,1,15), 10, 50),
          (dt.date(2019,1,16), 12, 50),
          (dt.date(2019,1,17), 12, 50),
        ],
        columns=['Timestamp','capacity_usd','used_usd']
      )

    # calculate
    bcs = BinCapUsed()
    bcs.handle_pre({'mainManager': FakeMm()})
    ctx = {'ec2_df': df1, 'ec2_dict': {'Region': 'us-west-2'}}
    bcs.per_ec2(ctx)
    bcs.per_ec2(ctx)

    # expected
    e = pd.DataFrame([
        (dt.date(2019,1,31), 68, 300, 2, frozenset(['us-west-2'])),
        (dt.date(2019,2,28),  0,   0, 0, frozenset([])),
        (dt.date(2019,3,31),  0,   0, 0, frozenset([])),
        (dt.date(2019,4,30),  0,   0, 0, frozenset([]))
      ],
      columns=['Timestamp', 'capacity_usd', 'used_usd', 'count_analyzed', 'regions_set']
    )
    e['Timestamp'] = pd.to_datetime(e['Timestamp'])
    e.set_index('Timestamp', inplace=True)

    # test expected = actual
    pd.testing.assert_frame_equal(e, bcs.df_bins)


  def test_3m(self, FakeMm):
    # prepare input
    s_ts = pd.date_range(start=dt.date(2019,1,15), end=dt.date(2019,4,15), freq='D')

    # parameters for simple case, no fluctuations
    cap1 = 10 # USD/day
    cap2 = 20 # USD/day

    #import numpy as np
    # s_used = np.random.rand(len(s_ts)) # random usage between 0 and 100%
    s_used = 0.3 # 30% usage

    # dataframes
    df1 = pd.DataFrame({
      'Timestamp': s_ts,
      'capacity_usd': cap1,
      'used_usd': s_used*cap1
    })
    df2 = pd.DataFrame({
      'Timestamp': s_ts,
      'capacity_usd': cap2,
      'used_usd': s_used*cap2
    })

    # int for simplicity
    df1['used_usd'] = df1['used_usd'].astype(int)
    df2['used_usd'] = df2['used_usd'].astype(int)

    # calculate
    bcs = BinCapUsed()
    bcs.handle_pre({'mainManager': FakeMm()})
    ctx1 = {'ec2_df': df1, 'ec2_dict': {'Region': 'us-west-2'}}
    bcs.per_ec2(ctx1)
    ctx2 = {'ec2_df': df2, 'ec2_dict': {'Region': 'us-west-2'}}
    bcs.per_ec2(ctx2)

    # expected
    e = pd.DataFrame([
        (dt.date(2019,1,31), 510, 153, 2, frozenset(['us-west-2'])),
        (dt.date(2019,2,28), 840, 252, 2, frozenset(['us-west-2'])),
        (dt.date(2019,3,31), 930, 279, 2, frozenset(['us-west-2'])),
        (dt.date(2019,4,30), 450, 135, 2, frozenset(['us-west-2']))
      ],
      columns=['Timestamp', 'capacity_usd', 'used_usd', 'count_analyzed', 'regions_set']
    )
    e['Timestamp'] = pd.to_datetime(e['Timestamp'])
    e.set_index('Timestamp', inplace=True)

    # test expected = actual
    pd.testing.assert_frame_equal(e, bcs.df_bins)



