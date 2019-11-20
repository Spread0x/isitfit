from isitfit.cost.redshift.pipeline_factory import redshift_cost_analyze, redshift_cost_optimize

import pytest

@pytest.mark.skip(reason="Need to figure out how to test this")
def test_costCore(mocker):
    mockee_list = [
      'isitfit.cost.redshift.iterator.RedshiftPerformanceIterator',
      'isitfit.cost.redshift.analyzer.CalculatorAnalyzeRedshift',
      'isitfit.cost.redshift.analyzer.CalculatorOptimizeRedshift',
      'isitfit.cost.redshift.reporter.ReporterAnalyze',
      'isitfit.cost.redshift.reporter.ReporterOptimize',
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
