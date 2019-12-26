from isitfit.cost.account_cost_optimize import ServiceReporter

class TestServiceReporterAppendDtCreated:
  def test_ok(self, mocker):
    # pandas fixture table
    import pandas as pd
    table_c = pd.DataFrame([
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
      }
    ])

    # context_all
    class ClickCtx:
      obj = {
        'aws_profile': 'test-profile'
      }
    context_all = {
      'click_ctx': ClickCtx()
    }

    # work within a new tempdir
    import tempfile
    with tempfile.TemporaryDirectory(prefix="isitfit-test-") as td:
      def mockreturn(*args, **kwargs): return td
      mocked_post = mocker.patch('isitfit.dotMan.DotMan.get_dotisitfit', side_effect=mockreturn)

      # 1st run, no sqlite exists yet
      sr = ServiceReporter()
      sr.table_c = table_c.iloc[:1].copy()
      sr.append_dtCreated(context_all)

      # assert only 1 set of dt_created
      tc_bkp1 = sr.table_c.copy()
      assert tc_bkp1.shape[0] == 1
      assert len(set(tc_bkp1.dt_created.to_list())) == 1

      # sleep x seconds
      import time
      time.sleep(2)

      # Add a new recommendation
      sr.table_c = table_c.iloc[:2].copy()
      sr.append_dtCreated(context_all)

      # assert 2 dates available
      tc_bkp2 = sr.table_c.copy()
      assert tc_bkp2.shape[0] == 2
      assert len(set(tc_bkp2.dt_created.to_list())) == 2

      # sleep x seconds
      time.sleep(2)

      # drop 1st 2 recommendations and create a 3rd new one
      sr.table_c = table_c.iloc[2:3].copy()
      sr.append_dtCreated(context_all)

      # assert 1 dates available
      tc_bkp3 = sr.table_c.copy()
      assert tc_bkp3.shape[0] == 1
      assert len(set(tc_bkp3.dt_created.to_list())) == 1

      # sleep x seconds
      time.sleep(2)

      # drop all recommendations and check code doesn't fail
      sr.table_c = table_c.iloc[0:0].copy()
      sr.append_dtCreated(context_all)

      # assert 0 dates available
      tc_bkp4 = sr.table_c.copy()
      assert tc_bkp4.shape[0] == 0
      # assert len(set(tc_bkp4.dt_created.to_list())) == 0 # How to deal with this?

      # sleep x seconds
      time.sleep(2)

      # bring back all 3 recomendations
      sr.table_c = table_c.iloc[0:3].copy()
      sr.append_dtCreated(context_all)

      # assert 3 dates available (i.e. the drop-all didn't wipe out the recommendations_previous table)
      # Update: actually, sticking with the simple method to update the recommendations_previous table,
      # which in fact wipes out the previous dates, and hence shows 1 single "new" date here
      tc_bkp5 = sr.table_c.copy()
      assert tc_bkp5.shape[0] == 3
      assert len(set(tc_bkp5.dt_created.to_list())) == 1 # not 3
