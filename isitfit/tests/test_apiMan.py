from moto import mock_sts
import pytest
from ..apiMan import ApiMan
from isitfit.cli.click_descendents import IsitfitCliError


@pytest.fixture(scope='function')
def MockRequestsRequest(mocker):
  def get_class(response):
    # set up
    def mockreturn(*args, **kwargs):
        return response
    mocker.patch('requests.request', side_effect=mockreturn)

    am = ApiMan(tryAgainIn=2, ctx=None)
    return am

  return get_class


class TestApiManRequest:
    @mock_sts
    def test_register_failSchemaL1(self, mocker, MockRequestsRequest):
        # since the MockApiManRequest patches the request function
        # and since the request function is
        response_val = {}
        class MockResponse:
          import json
          text = json.dumps(response_val)

        am = MockRequestsRequest(MockResponse)

        # trigger
        with pytest.raises(IsitfitCliError) as e:
            am.register()


    @mock_sts
    def test_register_failErrorGeneral(self, mocker, MockRequestsRequest):
        response_val = {'isitfitapi_status': {'code': 'error'}}
        class MockResponse:
          import json
          text = json.dumps(response_val)

        am = MockRequestsRequest(MockResponse)

        # trigger
        with pytest.raises(IsitfitCliError) as e:
            am.register()

#---------------------------

@pytest.fixture(scope='function')
def MockApiManRequest(mocker):
  def get_class(response):
    # set up
    def mockreturn(*args, **kwargs):
        return response, None
    mocker.patch('isitfit.apiMan.ApiMan.request', side_effect=mockreturn)

    am = ApiMan(tryAgainIn=2, ctx=None)
    return am

  return get_class


class TestApiManRegister:
    @mock_sts
    def test_register_failRegInProg(self, mocker, MockApiManRequest):
        response = {
                'isitfitapi_status': {'code': 'Registration in progress', 'description': 'foo'},
                'isitfitapi_body': {}
            }
        am = MockApiManRequest(response)
        am.nsecs_wait = 0

        # no exception, will not automatically try again
        am.call_n = 0
        am.tryAgainIn = 10
        am.register()

        # still no exception, will automatically try again till failing
        am.call_n = 1
        am.tryAgainIn = 2
        am.n_maxCalls = 5
        with pytest.raises(IsitfitCliError) as e:
          am.register()

        # triggers exception right away
        am.call_n = 2
        am.tryAgainIn = 2
        am.n_maxCalls = 3
        with pytest.raises(IsitfitCliError) as e:
            am.register()


    @mock_sts
    def test_register_failSchemaL2(self, mocker, MockApiManRequest):
        response = {
                'isitfitapi_status': {'code': 'ok', 'description': 'foo'},
                'isitfitapi_body': {
                }
            }
        am = MockApiManRequest(response)

        # exception
        with pytest.raises(IsitfitCliError) as e:
          am.register()


    @mock_sts
    def test_register_ok(self, mocker, MockApiManRequest):
        response = {
                'isitfitapi_status': {'code': 'ok', 'description': 'foo'},
                'isitfitapi_body': {
                    's3_arn': 'foo',
                    'sqs_url': 'foo',
                    'role_arn': '01234567890123456789',
                    's3_bucketName': 'foo',
                    's3_keyPrefix': 'foo',
                }
            }
        am = MockApiManRequest(response)

        # no exception
        am.register()
        assert True

