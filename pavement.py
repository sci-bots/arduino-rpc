from pprint import pprint
import sys

from paver.easy import task, needs, path, sh, cmdopts, options
from paver.setuputils import setup

sys.path.insert(0, '.')
import version


setup(name='arduino-rpc',
      version=version.getVersion(),
      description='Arduino RPC node packaged as Python package.',
      author='Christian Fobel',
      author_email='christian@fobel.net',
      url='http://github.com/wheeler-microfluidics/arduino_rpc.git',
      license='GPLv2',
      install_requires=['pandas>=0.15', 'nadamq>=0.8', 'path_helpers',
                        'clang_helpers>=0.3', 'c-array-defs>=0.1.post2',
                        'arduino-memory'],
      # Install data listed in `MANIFEST.in`
      include_package_data=True,
      packages=['arduino_rpc'])
