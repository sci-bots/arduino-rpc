from pprint import pprint
import sys

from paver.easy import task, needs, path, sh, cmdopts, options
from paver.setuputils import setup

sys.path.insert(0, '.')
import version


setup(name='wheeler.arduino_rpc',
      version=version.getVersion(),
      description='Arduino RPC node packaged as Python package.',
      author='Christian Fobel',
      author_email='christian@fobel.net',
      url='http://github.com/wheeler-microfluidics/arduino_rpc.git',
      license='GPLv2',
      install_requires=['nadamq>=0.5.post2', 'path_helpers',
                        'clang_helpers>=0.3', 'arduino-array',
                        'arduino-memory'],
      # Install data listed in `MANIFEST.in`
      include_package_data=True,
      packages=['arduino_rpc'])
