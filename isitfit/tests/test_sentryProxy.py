
def get_event_template():
  import os 
  dir_path = os.path.dirname(os.path.realpath(__file__))
  fn = os.path.join(dir_path, 'sentry_event.json')

  with open(fn,'r') as fh:
    et = fh.read()
    return et



def helper_sentryProxy(real_dsn):
    # init now with the object
    print("Test")
    from isitfit.sentry_proxy import init
    init(real_dsn)

    # trigger
    from sentry_sdk import capture_exception
    try:
        #1/0
        bla
    except Exception as e:
        capture_exception(e)


def test_sentry_proxy_fake():
    real_dsn = "https://foo@webhook.site/123456"
    helper_sentryProxy(real_dsn)
    assert True # no exception
    # sentry_sdk/transport.py#L135 should use the real_dsn above
    # MyDsn.to_auth should get called
    # How to test?


def test_sentry_proxy_isitfit():
    real_dsn = 'https://api-dev.isitfit.io/v0/fwd/sentry'
    helper_sentryProxy(real_dsn)
    assert True # no exception

