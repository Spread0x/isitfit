import pytest
from isitfit.cli.click_descendents import IsitfitCliError

@pytest.fixture(scope='function')
def MockEmailManFactory(mocker):
    def get_class(response_list):
        class MockRequest:
          def __init__(self, response_list):
            self.counter = 0
            self.response_list = response_list
          def __call__(self, *args, **kwargs):
            print("mock.api.request")
            self.counter += 1
            if self.counter > len(self.response_list):
              raise ValueError("Called mock request %i times, and list of provided responses is of length %i"%(self.counter, len(self.response_list)))
            response_single = self.response_list[self.counter-1]
            return response_single, None

        mock_func = MockRequest(response_list)
        mocker.patch('isitfit.apiMan.ApiMan.request', side_effect=mock_func)
        mocker.patch('isitfit.apiMan.ApiMan.register', side_effect=lambda: None)

        # prepare
        from ..emailMan import EmailMan
        em = EmailMan(None, None, None)
        return em

    return get_class


def isitfit_return_helper(code, description, body):
  return {'isitfitapi_status': {'code': code, 'description': description}, 'isitfitapi_body': body}


@pytest.fixture
def sendemail_fac(MockEmailManFactory):
  def factory(response_list):
    # build a fake click command so that the click.prompt will be emulated
    # https://click.palletsprojects.com/en/7.x/testing/?highlight=test#input-streams
    import click
    @click.command()
    def cmd():
      em = MockEmailManFactory(response_list)
      em.send(['foo@bar.com'])

    return cmd

  return factory


class TestEmailManSendWithInputStream:
  """
  Note: If this test seems to hang forever, it might be the case that the click.prompt is looping forever
  given the new-line inputs below
  """

  def test_send_verificationInProgress_okAfter1stAttempt(self, sendemail_fac):
    r1 = isitfit_return_helper('Email verification in progress', 'foo', None)
    r2 = isitfit_return_helper('ok', 'foo', {'from': 'bla'})
    sendemail_cmd = sendemail_fac([r1,r2])

    # trigger
    from click.testing import CliRunner
    runner = CliRunner()
    result = runner.invoke(sendemail_cmd, input='\n')
    print(result.__dict__) # in case of exception, this will show details
    assert not result.exception
    assert True # no exception


  def test_send_verificationInProgress_failsAfter3Attempts(self, sendemail_fac):
    r1 = isitfit_return_helper('Email verification in progress', 'foo', None)
    sendemail_cmd = sendemail_fac([r1,r1,r1])

    # trigger
    from click.testing import CliRunner
    runner = CliRunner()
    result = runner.invoke(sendemail_cmd, input='\n\n\n')
    print(result.__dict__) # in case of exception, this will show details
    assert result.exception
    assert type(result.exception).__name__ == 'ValueError'



class TestEmailManSendNoInput:
  """
  These tests do not use TestEmailManSendWithInputStream as they do not reach a click.prompt, so they don't need to handle the stream
  """
  def test_send_empty(self, MockEmailManFactory):
    ret = isitfit_return_helper('error', 'foo', None)
    em = MockEmailManFactory([ret])

    # trigger
    em.send([])
    assert True # no exception, nothing happens


  def test_send_failErrorGeneral(self, MockEmailManFactory):
    ret = isitfit_return_helper('error', 'foo', None)
    em = MockEmailManFactory([ret])

    # trigger
    with pytest.raises(IsitfitCliError) as e:
      em.send(['bla@foo.bar'])


  def test_send_failNotOk(self, MockEmailManFactory):
    ret = isitfit_return_helper('hey', 'foo', None)
    em = MockEmailManFactory([ret])

    # trigger
    with pytest.raises(IsitfitCliError) as e:
      em.send(['bla@foo.bar'])


  def test_send_failSchema(self, MockEmailManFactory):
    ret = isitfit_return_helper('ok', 'foo', {})
    em = MockEmailManFactory([ret])

    # trigger
    with pytest.raises(IsitfitCliError) as e:
      em.send(['bla@foo.bar'])


  def test_send_ok(self, MockEmailManFactory):
    ret = isitfit_return_helper('ok', 'foo', {'from': 'bla'})
    em = MockEmailManFactory([ret])

    # no trigger
    em.send(['bla@foo.bar'])
    assert True # no exception




