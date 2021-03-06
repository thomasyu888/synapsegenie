"""genie package setup"""
import os
from setuptools import setup, find_packages

# figure out the version
about = {}
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "synapsegenie", "__version__.py")) as f:
    exec(f.read(), about)

# Add readme
with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='synapsegenie',
      version=about["__version__"],
      description='Synapse flat file validation and processing pipeline',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://github.com/Sage-Bionetworks/Genie',
      author='Thomas Yu',
      author_email='thomas.yu@sagebionetworks.org',
      license='MIT',
      packages=find_packages(),
      zip_safe=False,
      python_requires='>=3.6',
      entry_points={'console_scripts': [
          'synapsegenie = synapsegenie.__main__:main'
      ]},
      install_requires=['pandas>=1.0',
                        'synapseclient>=2.0',
                        'httplib2>=0.11.3',
                        'pycrypto>=2.6.1',
                        'PyYAML>=5.1'])
