"""
Configure the sentry_sdk package to send HTTP requests to a custom endpoint
instead of the normal https://foo@sentry.io/1234 DSN

This is useful to intercept the sentry HTTP requests on a server
and then forward to the original sentry.io endpoint.
This way, the sentry key need not be exposed to the original client,
as would be the case if I use sentry_sdk directly in isitfit-cli.

Similar: https://github.com/getsentry/sentry/issues/1230

Usage:
  import sentry_proxy
  sentry_proxy.init(dsn="http://webhook.site/1234")
  
Tests:
  pytest isitfit/test_sentryProxy.py -k test_sentry_proxy_fake
  pytest isitfit/test_sentryProxy.py -k test_sentry_proxy_isitfit
"""

import sentry_sdk

# Setting the DSN doesn't work because of the validation
# SENTRY_SDK = "http://foo@webhook.site/5716352c-308a-45f1-b862-92ab80560cec"
# sentry_sdk.init(SENTRY_SDK)
#----------------------
# Create a derived sentry Dsn object
# since sentry_sdk.utils.Dsn.__init__ uses isinstance
# >>> class A: pass
# >>> class B(A): pass
# >>> x=B()
# >>> isinstance(x,B)
# True
# >>> isinstance(x,A)
# True
#-------------
from sentry_sdk.utils import Dsn, Auth
from sentry_sdk.transport import HttpTransport
import urllib.parse as urlparse


class MyAuth(Auth):
    @property
    def store_api_url(self):
      return self.real_dsn


class MyDsn(Dsn):
  def __init__(self, real_dsn):
    fake_dsn = "https://foo@sentry.io/1234"
    super().__init__(fake_dsn)

    parts = urlparse.urlsplit(real_dsn)
    self.scheme = parts.scheme
    self.host = parts.hostname
    self.port = parts.port or (parts.scheme == "https" and 443 or 80)
    self.public_key = None
    self.secret_key = None
    self.project_id = None
    self.path = parts.path
    self.real_dsn = real_dsn # new variable for the sake of to_auth below


  def to_auth(self, client=None):
        # over-write function
        auth = super().to_auth(client)
        # add member
        auth.real_dsn = self.real_dsn
        # cast class to use new member
        auth.__class__ = MyAuth
        return auth


class MyTransport(HttpTransport):
  def __init__(self, options=None):
    super().__init__(options)
    # cast http://stackoverflow.com/questions/3464061/ddg#3464154
    self.parsed_dsn.__class__ = MyDsn
    # save self._auth again
    self._auth = self.parsed_dsn.to_auth("sentry-proxy.python/v0")


def init(dsn):
    # use default_integrations=False to avoid the AtexitIntegration from displaying a message
    # "Senty is attempting to send ..."
    # https://docs.sentry.io/platforms/python/default-integrations/
    parsed_dsn = MyDsn(dsn)
    sentry_sdk.init(dsn=parsed_dsn, transport=MyTransport, default_integrations=False)

