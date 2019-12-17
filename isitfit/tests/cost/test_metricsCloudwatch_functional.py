from isitfit.cost.metrics_cloudwatch import CloudwatchAssistant, NoCloudwatchException

import pytest

class TestCwAssFunctional:
  def test_tableauDesktopInstance_noData(self):
    import datetime as dt
    dtnow = dt.datetime.now()

    ca = CloudwatchAssistant()
    ca.set_resource("us-west-2")
    assert True # no exception

    iid = 'i-05a61a1d9c3d208b3'
    it = ca.id2iterator(iid, 'AWS/EC2', 'InstanceId')
    assert it is not None

    with pytest.raises(NoCloudwatchException):
      me = ca.iterator2metric(it, iid)


  def test_inexistantId(self):
    import datetime as dt
    dtnow = dt.datetime.now()

    ca = CloudwatchAssistant()
    ca.set_resource("us-west-2")
    assert True # no exception

    iid = 'i-123456'
    it = ca.id2iterator(iid, 'AWS/EC2', 'InstanceId')
    assert it is not None

    with pytest.raises(NoCloudwatchException):
      me = ca.iterator2metric(it, iid)


  def test_newInstance_ndays90(self):
    """
    Run this after creating an instance manually
    (with spot using isitfit/tests/cost/ec2/test_functional.sh)
    and then plugging in the ID here
    """
    import datetime as dt
    dtnow = dt.datetime.now()

    ca = CloudwatchAssistant()
    ca.set_resource("us-west-2")
    assert True # no exception

    iid = 'i-0554591aacf06353a' # <<<<<<<< ID of newly created instance here
    it = ca.id2iterator(iid, 'AWS/EC2', 'InstanceId')
    assert it is not None

    me = ca.iterator2metric(it, iid)
    assert me is not None

    # test with ndays=90
    ca.set_ndays(90)
    st90 = ca.metric2stats(me)
    assert st90 is not None
    # for ndays=90, this is not a reliable assertion
    # assert st90['Datapoints'][0]['Timestamp'].date() == dtnow.date()

    df90 = ca.stats2df(st90, iid, dtnow)
    assert df90 is not None
    assert df90.shape[0] == 1
    # this gets corrected if cloudwatch returns a past timestamp for an instance created today
    assert df90.Timestamp.iloc[0] == dtnow.date()

    # test with ndays=7
    ca.set_ndays(7)
    st07 = ca.metric2stats(me)
    assert st07 is not None
    # for ndays=7, this is always failing
    assert st07['Datapoints'][0]['Timestamp'].date() != dtnow.date()

    df07 = ca.stats2df(st07, iid, dtnow)
    assert df07 is not None
    assert df07.shape[0] == 1
    # stats2df will fix the wrong timestamp
    assert df07.Timestamp.iloc[0] == dtnow.date()
