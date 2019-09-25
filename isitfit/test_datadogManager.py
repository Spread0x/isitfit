from .datadogManager import DatadogManager

def test_datadogman_1():
    ddg = DatadogManager()
    host_id='i-0f31feed76f7fb07c'
    df_all = ddg.get_metrics_all(host_id=host_id)
    assert df_all.shape[0] > 0
    #import pdb
    #pdb.set_trace()
    #print(df_all.head())

