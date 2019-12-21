import pytest

# https://stackoverflow.com/a/40884671/4126114
@pytest.mark.parametrize("real_dsn", ["https://foo@webhook.site/123456", 'https://api-dev.isitfit.io/v0/fwd/sentry'])
def test_sentryProxy(real_dsn):
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

    assert True # no exception
    # sentry_sdk/transport.py#L135 should use the real_dsn above
    # MyDsn.to_auth should get called
    # How to test?

