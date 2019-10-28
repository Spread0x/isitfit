from moto import mock_sts
import pytest
from ..apiMan import ApiMan
from ..utils import IsitfitCliError


@pytest.fixture(scope='function')
def MockApiManFactory(mocker):
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
    def test_register_failSchemaL1(self, mocker, MockApiManFactory):
        am = MockApiManFactory({})

        # trigger
        with pytest.raises(IsitfitCliError) as e:
            am.register()


    @mock_sts
    def test_register_failErrorGeneral(self, mocker, MockApiManFactory):
        response = {'isitfitapi_status': {'code': 'error'}}
        am = MockApiManFactory(response)

        # trigger
        with pytest.raises(IsitfitCliError) as e:
            am.register()


    @mock_sts
    def test_register_failRegInProg(self, mocker, MockApiManFactory):
        response = {
                'isitfitapi_status': {'code': 'Registration in progress', 'description': 'foo'},
                'isitfitapi_body': {}
            }
        am = MockApiManFactory(response)
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
    def test_register_failSchemaL2(self, mocker, MockApiManFactory):
        response = {
                'isitfitapi_status': {'code': 'ok', 'description': 'foo'},
                'isitfitapi_body': {
                }
            }
        am = MockApiManFactory(response)

        # exception
        with pytest.raises(IsitfitCliError) as e:
          am.register()


    @mock_sts
    def test_register_ok(self, mocker, MockApiManFactory):
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
        am = MockApiManFactory(response)

        # no exception
        am.register()
        assert True

