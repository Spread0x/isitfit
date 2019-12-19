# 2019-10-24 Not sure why find_packages was commented out .. bringing it back
from setuptools import setup, find_packages

# copied from https://github.com/awslabs/git-remote-codecommit/blob/master/setup.py
import os
def read(fname):
  return open(os.path.join(os.path.dirname(__file__), fname)).read()
  

from isitfit import isitfit_version

# follow https://github.com/awslabs/git-remote-codecommit/blob/master/setup.py
# and https://packaging.python.org/tutorials/packaging-projects/
setup(
    name='isitfit',
    version=isitfit_version,
    author="Shadi Akiki, AutofitCloud",
    author_email="shadi@autofitcloud.com",
    url='https://gitlab.com/autofitcloud/isitfit',
    description="Command-line tool to calculate excess AWS cloud resource capacity",

    # 2019-09-10 not sure what in the README.md is yielding the twine error
    # The description failed to render in the default format of reStructuredText.
    # long_description = read('README.md'),
    long_description = 'Check https://isitfit.autofitcloud.com',
    long_description_content_type="text/markdown",
    
    packages=find_packages(),
    # packages = ['isitfit'],
    include_package_data=True,
    install_requires=[
        'click==7.0',
        'pandas==0.25.1',
        'requests==2.22.0',
        'cachecontrol==0.12.5',
        'lockfile==0.12.2',
        'tabulate==0.8.3',
        'termcolor==1.1.0',
        'tqdm==4.32.2',

        'redis==3.3.8',
        'pyarrow==0.15.0',

        # check note in requirements.txt
        'awscli==1.16.248',
        'boto3==1.9.238',

        'datadog==0.30.0',
        'schema==0.7.1',
        'visidata==1.5.2',
        'outdated==0.2.0',
        'aws-requests-auth==0.4.2',
        'matomo_sdk_py==0.2.1',
        'simple-cache==0.35',

        # Before upgrading this, it's very important to test that my sentry_proxy.py code works with the new version
        'sentry-sdk==0.13.5'
    ],
    entry_points='''
        [console_scripts]
        isitfit=isitfit.cli.core:cli_core
    ''',
)
