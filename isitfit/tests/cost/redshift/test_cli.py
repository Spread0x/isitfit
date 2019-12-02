from isitfit.cost.redshift_analyze import  pipeline_factory as redshift_cost_analyze
from isitfit.cost.redshift_optimize import pipeline_factory as redshift_cost_optimize


import pytest

@pytest.mark.skip(reason="Need to figure out how to test this")
def test_costCore(mocker):
    mockee_list = [
      'isitfit.cost.redshift_analyze.RedshiftPerformanceIterator',
      'isitfit.cost.redshift_analyze.CalculatorAnalyzeRedshift',
      'isitfit.cost.redshift_optimize.CalculatorOptimizeRedshift',
      'isitfit.cost.redshift_analyze.ReporterAnalyze',
      'isitfit.cost.redshift_optimize.ReporterOptimize',
    ]
    for mockee_single in mockee_list:
      mocker.patch(mockee_single, autospec=True)

    # specific mocks
    # mocker.patch('isitfit.cost.redshift.iterator.RedshiftPerformanceIterator.count', side_effect=lambda: 1)

    # run and test
    redshift_cost_analyze(None)
    assert True # no exception

    redshift_cost_analyze([1])
    assert True # no exception

    redshift_cost_optimize()
    assert True # no exception
