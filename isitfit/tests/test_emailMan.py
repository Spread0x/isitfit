import pytest
from ..utils import IsitfitCliError

@pytest.fixture(scope='function')
def MockEmailManFactory(mocker):
    def get_class(error_code, body):
        def mockreturn(*args, **kwargs):
            response = {'isitfitapi_status': {'code': error_code, 'description': 'foo'}, 'isitfitapi_body': body}
            return response, None

        mocker.patch('isitfit.apiMan.ApiMan.request', side_effect=mockreturn)
        mocker.patch('isitfit.apiMan.ApiMan.register', side_effect=lambda: None)

        # prepare
        from ..emailMan import EmailMan
        em = EmailMan(None, None, None)
        return em

    return get_class


def test_send_failVerificationInProgress(MockEmailManFactory):
    em = MockEmailManFactory('Email verification in progress', None)

    # trigger
    with pytest.raises(IsitfitCliError) as e:
      em.send([])


def test_send_failErrorGeneral(MockEmailManFactory):
    em = MockEmailManFactory('error', None)

    # trigger
    with pytest.raises(IsitfitCliError) as e:
      em.send([])


def test_send_failNotOk(MockEmailManFactory):
    em = MockEmailManFactory('hey', None)

    # trigger
    with pytest.raises(IsitfitCliError) as e:
      em.send([])


def test_send_failSchema(MockEmailManFactory):
    em = MockEmailManFactory('ok', {})

    # trigger
    with pytest.raises(IsitfitCliError) as e:
      em.send([])


def test_send_ok(MockEmailManFactory):
    em = MockEmailManFactory('ok', {'from': 'bla'})

    # no trigger
    em.send([])
    assert True # no exception
