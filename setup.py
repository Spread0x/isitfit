from setuptools import setup # , find_packages

# copied from https://github.com/awslabs/git-remote-codecommit/blob/master/setup.py
import os
def read(fname):
  return open(os.path.join(os.path.dirname(__file__), fname)).read()
  

# follow https://github.com/awslabs/git-remote-codecommit/blob/master/setup.py
# and https://packaging.python.org/tutorials/packaging-projects/
setup(
    name='isitfit',
    version='0.1.4',
    author="Shadi Akiki, AutofitCloud",
    author_email="shadi@autofitcloud.com",
    url='https://gitlab.com/autofitcloud/isitfit',
    description="Command-line tool to calculate excess AWS cloud resource capacity",
    long_description = read('README.md'),
    long_description_content_type="text/markdown",
    
    # packages=find_packages(),
    packages = ['isitfit'],
    include_package_data=True,
    install_requires=[
        'click==7.0',
        'pandas==0.25.1',
        'requests==2.22.0',
        'boto3==1.9.219',
        'cachecontrol==0.12.5',
        'lockfile==0.12.2',
        'git-remote-aws==0.5.2',
        'tabulate==0.8.3'
    ],
    entry_points='''
        [console_scripts]
        isitfit=isitfit.cli:cli
    ''',
)
