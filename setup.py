# -*- coding: utf-8 -*-

import os
import sys
from shutil import rmtree

from setuptools import setup, Command

here = os.path.abspath(os.path.dirname(__file__))

with open("README.rst", "rb") as f:
    long_descr = f.read().decode("utf-8")

class PublishCommand(Command):
    """Support setup.py publish."""

    description = 'Build and publish the package.'
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('Removing previous builds…')
            rmtree(os.path.join(here, 'dist'))
        except:
            pass

        self.status('Building Source and Wheel (universal) distribution…')
        os.system('{0} setup.py sdist bdist_wheel --universal'.format(sys.executable))

        self.status('Uploading the package to PyPi via Twine…')
        os.system('twine upload dist/*')

        sys.exit()


setup(
    name="github_traffic_stats",
    packages=["gts"],
    long_description=long_descr,
    entry_points={
        "console_scripts": ['gts = gts.main:main']
    },
    version='1.2.0',
    keywords=['github', 'traffic', 'api'],
    description="Get statistics on web traffic to your GitHub repositories.",
    author="Niel Chah, Anthony Bloomer",
    url="https://github.com/nchah/github-traffic-stats",
    install_requires=[
        'requests'
    ],
    classifiers=[
        'Intended Audience :: Developers',
    ],
    cmdclass={
        'publish': PublishCommand,
    }
)