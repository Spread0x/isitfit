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
        (dt.date(2019,1,31), 0, 0, 0, frozenset([]), dt.date(2019,1,31), dt.date(2019,1,1), ),
        (dt.date(2019,2,28), 0, 0, 0, frozenset([]), dt.date(2019,2,28), dt.date(2019,2,1), ),
        (dt.date(2019,3,31), 0, 0, 0, frozenset([]), dt.date(2019,3,31), dt.date(2019,3,1), ),
        (dt.date(2019,4,30), 0, 0, 0, frozenset([]), dt.date(2019,4,30), dt.date(2019,4,1), ),
      ],
      columns=['Timestamp', 'capacity_usd', 'used_usd', 'count_analyzed', 'regions_set', 'dt_start', 'dt_end']
    )
    for fx in ['Timestamp', 'dt_start', 'dt_end']: e[fx] = pd.to_datetime(e[fx])
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
        (dt.date(2019,1,31), 68, 300, 2, frozenset(['us-west-2']), dt.date(2019,1,15), dt.date(2019,1,17), ),
        (dt.date(2019,2,28),  0,   0, 0, frozenset([]),            dt.date(2019,2,28), dt.date(2019,2, 1), ),
        (dt.date(2019,3,31),  0,   0, 0, frozenset([]),            dt.date(2019,3,31), dt.date(2019,3, 1), ),
        (dt.date(2019,4,30),  0,   0, 0, frozenset([]),            dt.date(2019,4,30), dt.date(2019,4, 1), ),
      ],
      columns=['Timestamp', 'capacity_usd', 'used_usd', 'count_analyzed', 'regions_set', 'dt_start', 'dt_end']
    )
    for fx in ['Timestamp', 'dt_start', 'dt_end']: e[fx] = pd.to_datetime(e[fx])
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
        (dt.date(2019,1,31), 510, 153, 2, frozenset(['us-west-2']), dt.date(2019,1,15), dt.date(2019,1,31), ),
        (dt.date(2019,2,28), 840, 252, 2, frozenset(['us-west-2']), dt.date(2019,2, 1), dt.date(2019,2,28), ),
        (dt.date(2019,3,31), 930, 279, 2, frozenset(['us-west-2']), dt.date(2019,3, 1), dt.date(2019,3,31), ),
        (dt.date(2019,4,30), 450, 135, 2, frozenset(['us-west-2']), dt.date(2019,4, 1), dt.date(2019,4,15), ),
      ],
      columns=['Timestamp', 'capacity_usd', 'used_usd', 'count_analyzed', 'regions_set', 'dt_start', 'dt_end']
    )
    for fx in ['Timestamp', 'dt_start', 'dt_end']: e[fx] = pd.to_datetime(e[fx])
    e.set_index('Timestamp', inplace=True)

    # test expected = actual
    pd.testing.assert_frame_equal(e, bcs.df_bins)


class TestBinCapUsedAfterAll:
  def test_preNoBreak(self, FakeMm):
    bcs = BinCapUsed()
    ret = bcs.handle_pre({'mainManager': FakeMm()})
    assert ret is not None

  def test_3m(self, FakeMm):
    bcs = BinCapUsed()
    bcs.handle_pre({'mainManager': FakeMm()})
    bcs.after_all({})

    import numpy as np
    e = pd.DataFrame([
        (dt.date(2019,1,31), 0, 0, 0, frozenset([]), np.nan, np.nan, 0, '0', ),
        (dt.date(2019,2,28), 0, 0, 0, frozenset([]), np.nan, np.nan, 0, '0', ),
        (dt.date(2019,3,31), 0, 0, 0, frozenset([]), np.nan, np.nan, 0, '0', ),
        (dt.date(2019,4,30), 0, 0, 0, frozenset([]), np.nan, np.nan, 0, '0', ),
      ],
      columns=['Timestamp', 'capacity_usd', 'used_usd', 'count_analyzed', 'regions_set', 'dt_start', 'dt_end', 'used_pct', 'regions_str']
    )
    for fx in ['Timestamp', 'dt_start', 'dt_end']: e[fx] = pd.to_datetime(e[fx])
    e.set_index('Timestamp', inplace=True)

    pd.testing.assert_frame_equal(e, bcs.df_bins)



@pytest.fixture
def example_dataframe():
    import datetime as dt
    d = pd.date_range(dt.date(2019,9,1), dt.date(2019,12,1))
    df = pd.DataFrame({'Timestamp': d, 'a': range(len(d))})
    df['Timestamp'] = pd.to_datetime(df.Timestamp)
    dt_start = df.Timestamp.min()
    dt_end = df.Timestamp.max()
    df = df.set_index('Timestamp')
    return df, dt_start, dt_end


class TestBinCapUsedResample:
  def test_07d(self, example_dataframe):
    dfi, dt_start, dt_end = example_dataframe

    bcs = BinCapUsed()
    bcs._set_freq(7)

    dfe_actual = bcs.do_resample_end(dfi).sum()
    dfs_actual = bcs.do_resample_start(dfi).sum()
    #dfe_actual = bcs.fix_resample_end(dfe_actual, dfs_actual)
    #dfs_actual = bcs.fix_resample_start(dfs_actual, dfe_actual, dt_start, dt_end)

    idxs_expected = pd.date_range(dt.date(2019,9,1), dt.date(2019,12,1))
    assert (dfs_actual.index == idxs_expected).all()

    # notice this is different than the "df_daily.resample('1D', label='right')" below
    idxe_expected = pd.date_range(dt.date(2019,9,1), dt.date(2019,12,1))
    assert (dfe_actual.index == idxe_expected).all()


  def test_30d(self, example_dataframe):
    dfi, dt_start, dt_end = example_dataframe

    bcs = BinCapUsed()
    bcs._set_freq(30)

    dfe_actual = bcs.do_resample_end(dfi).sum()
    dfs_actual = bcs.do_resample_start(dfi).sum()
    #dfe_actual = bcs.fix_resample_end(dfe_actual, dfs_actual)
    #dfs_actual = bcs.fix_resample_start(dfs_actual, dfe_actual, dt_start, dt_end)

    idxs_expected = [
      dt.date(2019, 8,26),
      dt.date(2019, 9, 2), dt.date(2019, 9, 9), dt.date(2019, 9,16), dt.date(2019, 9,23),
      dt.date(2019, 9,30),
      dt.date(2019,10, 7), dt.date(2019,10,14), dt.date(2019,10,21), dt.date(2019,10,28),
      dt.date(2019,11, 4), dt.date(2019,11,11), dt.date(2019,11,18), dt.date(2019,11,25),
    ]
    assert (dfs_actual.index == idxs_expected).all()

    idxe_expected = [
      dt.date(2019, 9, 1), dt.date(2019, 9, 8), dt.date(2019, 9,15), dt.date(2019, 9,22),
      dt.date(2019, 9,29),
      dt.date(2019,10, 6), dt.date(2019,10,13), dt.date(2019,10,20), dt.date(2019,10,27),
      dt.date(2019,11, 3), dt.date(2019,11,10), dt.date(2019,11,17), dt.date(2019,11,24),
      dt.date(2019,12, 1),
    ]
    assert (dfe_actual.index == idxe_expected).all()


  def test_60d(self, example_dataframe):
    dfi, dt_start, dt_end = example_dataframe

    bcs = BinCapUsed()
    bcs._set_freq(60)

    dfe_actual = bcs.do_resample_end(dfi).sum()
    dfs_actual = bcs.do_resample_start(dfi).sum()
    #dfe_actual = bcs.fix_resample_end(dfe_actual, dfs_actual)
    #dfs_actual = bcs.fix_resample_start(dfs_actual, dfe_actual, dt_start, dt_end)

    idxs_expected = [
      dt.date(2019, 9, 1), dt.date(2019, 9,15),
      dt.date(2019,10, 1), dt.date(2019,10,15),
      dt.date(2019,11, 1), dt.date(2019,11,15),
      dt.date(2019,12, 1),
    ]
    assert (dfs_actual.index == idxs_expected).all()

    # notice this is different than idx_exp_1SM_right_right below
    # Update 2019-12-17 without the fix_resample_* function, this is the same as idx_exp_1SM_right_right
    #idxe_expected = [
    #  dt.date(2019, 9,14), dt.date(2019, 9,30),
    #  dt.date(2019,10,14), dt.date(2019,10,31),
    #  dt.date(2019,11,14), dt.date(2019,11,30),
    #  dt.date(2019,12,14),
    #]
    idxe_expected = [
      dt.date(2019, 9,15), dt.date(2019, 9,30),
      dt.date(2019,10,15), dt.date(2019,10,31),
      dt.date(2019,11,15), dt.date(2019,11,30),
      dt.date(2019,12,15),
    ]
    assert (dfe_actual.index == idxe_expected).all()


  def test_90d(self, example_dataframe):
    dfi, dt_start, dt_end = example_dataframe

    bcs = BinCapUsed()
    bcs._set_freq(90)

    dfe_actual = bcs.do_resample_end(dfi).sum()
    dfs_actual = bcs.do_resample_start(dfi).sum()
    #dfe_actual = bcs.fix_resample_end(dfe_actual, dfs_actual)
    #dfs_actual = bcs.fix_resample_start(dfs_actual, dfe_actual, dt_start, dt_end)

    idxs_expected = [
      dt.date(2019, 9, 1),
      dt.date(2019,10, 1),
      dt.date(2019,11, 1),
      dt.date(2019,12, 1),
    ]
    assert (dfs_actual.index == idxs_expected).all()

    idxe_expected = [
      dt.date(2019, 9,30),
      dt.date(2019,10,31),
      dt.date(2019,11,30),
      dt.date(2019,12,31),
    ]
    assert (dfe_actual.index == idxe_expected).all()



class TestPandasResample:
  """
  General tests on pandas resample method
  """
  def test_resample(self, example_dataframe):
    """
    Setting closed=... only affects 1 case (check comments below)
    """
    df_daily, dt_start, dt_end = example_dataframe

    # expected indeces
    idx_exp_1WMON_left_left = [
      dt.date(2019, 8,26),
      dt.date(2019, 9, 2), dt.date(2019, 9, 9), dt.date(2019, 9,16), dt.date(2019, 9,23),
      dt.date(2019, 9,30),
      dt.date(2019,10, 7), dt.date(2019,10,14), dt.date(2019,10,21), dt.date(2019,10,28),
      dt.date(2019,11, 4), dt.date(2019,11,11), dt.date(2019,11,18), dt.date(2019,11,25),
    ]
    col_exp_1WMON_left_left = [
      0,
      28, 77, 126, 175,
      224,
      273, 322, 371, 420,
      469, 518, 567, 616,
    ]
    df_exp_1WMON_left_left = pd.DataFrame({'a': col_exp_1WMON_left_left, 'Timestamp': idx_exp_1WMON_left_left})
    df_exp_1WMON_left_left['Timestamp'] = pd.to_datetime(df_exp_1WMON_left_left.Timestamp)
    df_exp_1WMON_left_left.set_index('Timestamp', inplace=True)

    col_exp_1WMON_left_skip = [
      1,
      35, 84, 133, 182,
      231,
      280, 329, 378, 427,
      476, 525, 574, 531,
    ]
    df_exp_1WMON_left_skip = pd.DataFrame({'a': col_exp_1WMON_left_skip, 'Timestamp': idx_exp_1WMON_left_left})
    df_exp_1WMON_left_skip['Timestamp'] = pd.to_datetime(df_exp_1WMON_left_skip.Timestamp)
    df_exp_1WMON_left_skip.set_index('Timestamp', inplace=True)


    idx_exp_1WSUN_right_right = [
      dt.date(2019, 9, 1), dt.date(2019, 9, 8), dt.date(2019, 9,15), dt.date(2019, 9,22),
      dt.date(2019, 9,29),
      dt.date(2019,10, 6), dt.date(2019,10,13), dt.date(2019,10,20), dt.date(2019,10,27),
      dt.date(2019,11, 3), dt.date(2019,11,10), dt.date(2019,11,17), dt.date(2019,11,24),
      dt.date(2019,12, 1),
    ]

    idx_exp_1SMS_left_left = [
      dt.date(2019, 9, 1), dt.date(2019, 9,15),
      dt.date(2019,10, 1), dt.date(2019,10,15),
      dt.date(2019,11, 1), dt.date(2019,11,15),
      dt.date(2019,12, 1),
    ]

    # notice this is different than test_60d above
    idx_exp_1SM_right_right = [
      dt.date(2019, 9,15), dt.date(2019, 9,30),
      dt.date(2019,10,15), dt.date(2019,10,31),
      dt.date(2019,11,15), dt.date(2019,11,30),
      dt.date(2019,12,15),
    ]

    idx_exp_1MS_left_left = [
      dt.date(2019, 9, 1),
      dt.date(2019,10, 1),
      dt.date(2019,11, 1),
      dt.date(2019,12, 1),
    ]

    idx_exp_1M_right_right = [
      dt.date(2019, 9,30),
      dt.date(2019,10,31),
      dt.date(2019,11,30),
      dt.date(2019,12,31),
    ]


    # 1D should be the same
    df_resampled = df_daily.resample('1D', label='left', closed='left').sum()
    pd.testing.assert_frame_equal(df_daily, df_resampled)
    assert (df_daily.index == df_resampled.index).all()

    # again but skip closed
    df_resampled = df_daily.resample('1D', label='left').sum()
    pd.testing.assert_frame_equal(df_daily, df_resampled)
    assert (df_daily.index == df_resampled.index).all()

    # again with right
    df_resampled = df_daily.resample('1D', label='right', closed='right').sum()
    pd.testing.assert_frame_equal(df_daily, df_resampled)
    assert (df_daily.index == df_resampled.index).all()

    # again with right, but without setting closed
    df_resampled = df_daily.resample('1D', label='right').sum()
    # pd.testing.assert_frame_equal(df_daily, df_resampled)
    assert not (df_daily.index == df_resampled.index).all() # <<<<<<<<<<<< notice expected difference

    # 1W-MON
    df_resampled = df_daily.resample('1W-MON', label='left', closed='left').sum()
    assert (idx_exp_1WMON_left_left == df_resampled.index).all()
    pd.testing.assert_frame_equal(df_exp_1WMON_left_left, df_resampled)

    # again with skip closed
    df_resampled = df_daily.resample('1W-MON', label='left').sum()
    assert (idx_exp_1WMON_left_left == df_resampled.index).all()
    pd.testing.assert_frame_equal(df_exp_1WMON_left_skip, df_resampled) # <<<<<<<<<<<<< notice eventhough the index is the same, the summed values are different

    # 1W-SUN
    df_resampled = df_daily.resample('1W-SUN', label='right', closed='right').sum()
    assert (idx_exp_1WSUN_right_right == df_resampled.index).all()

    # again with skip closed
    df_resampled = df_daily.resample('1W-SUN', label='right').sum()
    assert (idx_exp_1WSUN_right_right == df_resampled.index).all()

    # 1SMS
    df_resampled = df_daily.resample('1SMS', label='left', closed='left').sum()
    assert (idx_exp_1SMS_left_left == df_resampled.index).all()

    # again with skip closed
    df_resampled = df_daily.resample('1SMS', label='left').sum()
    assert (idx_exp_1SMS_left_left == df_resampled.index).all()

    # 1SM
    df_resampled = df_daily.resample('1SM', label='right', closed='right').sum()
    assert (idx_exp_1SM_right_right == df_resampled.index).all()

    # again with skip closed
    df_resampled = df_daily.resample('1SM', label='right').sum()
    assert (idx_exp_1SM_right_right == df_resampled.index).all()

    # 1MS
    df_resampled = df_daily.resample('1MS', label='left', closed='left').sum()
    assert (idx_exp_1MS_left_left == df_resampled.index).all()

    # again with skip closed
    df_resampled = df_daily.resample('1MS', label='left').sum()
    assert (idx_exp_1MS_left_left == df_resampled.index).all()

    # 1M
    df_resampled = df_daily.resample('1M', label='right', closed='right').sum()
    assert (idx_exp_1M_right_right == df_resampled.index).all()

    # again with skip closed
    df_resampled = df_daily.resample('1M', label='right').sum()
    assert (idx_exp_1M_right_right == df_resampled.index).all()

