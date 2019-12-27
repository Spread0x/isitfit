def getnow():
    # date now
    import datetime as dt
    import pytz
    dtnow = dt.datetime.utcnow().replace(tzinfo=pytz.utc)
    return dtnow


class TestSqliteManUpdateDtCreated:
  def test_ok(self, mocker):
    # date now
    import datetime as dt
    import pytz
    dtnow = dt.datetime.utcnow().replace(tzinfo=pytz.utc)

    # pandas fixture table
    import pandas as pd
    table_fixture = pd.DataFrame([
      {'service': 'EC2',
       'region': 'us-west-2',
       'resource_id': 'i-1',
       'resource_size1': 't3.medium',
       'resource_size2': None,
       'classification_1': 'Underused',
       'classification_2': 'No ram',
       'cost_3m': 106,
       'recommended_size1': 't3.small',
       'savings': -53,
       'tags': [1,2,3],
       #'dt_detected': dtnow,
      },
      {'service': 'EC2',
       'region': 'us-west-2',
       'resource_id': 'i-2',
       'resource_size1': 't3.medium',
       'resource_size2': None,
       'classification_1': 'Underused',
       'classification_2': 'No ram',
       'cost_3m': 106,
       'recommended_size1': 't3.small',
       'savings': -53,
       'tags': [1,2,3],
       #'dt_detected': dtnow,
      },
      {'service': 'EC2',
       'region': 'us-west-2',
       'resource_id': 'i-3',
       'resource_size1': 't3.medium',
       'resource_size2': None,
       'classification_1': 'Underused',
       'classification_2': 'No ram',
       'cost_3m': 106,
       'recommended_size1': 't3.small',
       'savings': -53,
       'tags': [1,2,3],
       #'dt_detected': dtnow,
      }
    ])

    # context_all
    class ClickCtx:
      obj = {
        'aws_profile': 'test-profile'
      }

    context_all = {
    }

    # work within a new tempdir
    import tempfile
    with tempfile.TemporaryDirectory(prefix="isitfit-test-") as td:
      def mockreturn(*args, **kwargs): return td
      mocked_post = mocker.patch('isitfit.dotMan.DotMan.get_dotisitfit', side_effect=mockreturn)

      # init
      import time
      from isitfit.cost.account_cost_optimize import SqliteMan
      click_ctx = ClickCtx()
      sr = SqliteMan(click_ctx)

      # 1st run, no sqlite exists yet, assert only 1 value of dt_detected
      table_fixture['dt_detected'] = getnow()
      context_all['table_c'] = table_fixture.iloc[:1].copy()
      context_all = sr.update_dtCreated(context_all)

      tc_bkp1 = context_all['table_c'].copy()
      assert tc_bkp1.shape[0] == 1
      assert len(set(tc_bkp1.dt_detected.to_list())) == 1

      # sleep x seconds
      time.sleep(2)

      # Add a new recommendation, assert 2 dates available
      table_fixture['dt_detected'] = getnow()
      context_all['table_c'] = table_fixture.iloc[:2].copy()
      context_all = sr.update_dtCreated(context_all)

      tc_bkp2 = context_all['table_c'].copy()
      assert tc_bkp2.shape[0] == 2
      assert len(set(tc_bkp2.dt_detected.to_list())) == 2

      # sleep x seconds
      time.sleep(2)

      # drop 1st 2 recommendations and create a 3rd new one, assert 1 dates available
      table_fixture['dt_detected'] = getnow()
      context_all['table_c'] = table_fixture.iloc[2:3].copy()
      context_all = sr.update_dtCreated(context_all)

      tc_bkp3 = context_all['table_c'].copy()
      assert tc_bkp3.shape[0] == 1
      assert len(set(tc_bkp3.dt_detected.to_list())) == 1

      # sleep x seconds
      time.sleep(2)

      # drop all recommendations and check code doesn't fail, assert 0 dates available
      table_fixture['dt_detected'] = getnow()
      context_all['table_c'] = table_fixture.iloc[0:0].copy()
      context_all = sr.update_dtCreated(context_all)

      tc_bkp4 = context_all['table_c'].copy()
      assert tc_bkp4.shape[0] == 0
      # assert len(set(tc_bkp4.dt_detected.to_list())) == 0 # How to deal with this?

      # sleep x seconds
      time.sleep(2)

      # bring back all 3 recomendations, assert 3 dates available (i.e. the drop-all didn't wipe out the recommendations_previous table)
      # Update: actually, sticking with the simple method to update the recommendations_previous table,
      # which in fact wipes out the previous dates, and hence shows 1 single "new" date here
      table_fixture['dt_detected'] = getnow()
      context_all['table_c'] = table_fixture.iloc[0:3].copy()
      context_all = sr.update_dtCreated(context_all)

      tc_bkp5 = context_all['table_c'].copy()
      assert tc_bkp5.shape[0] == 3
      assert len(set(tc_bkp5.dt_detected.to_list())) == 1 # not 3
