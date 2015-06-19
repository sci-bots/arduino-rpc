from pprint import pprint
import sys

from paver.easy import task, needs, path, sh, cmdopts, options
from paver.setuputils import setup, find_package_data

sys.path.insert(0, '.')
import version


arduino_rpc_files = find_package_data(package='arduino_rpc',
                                      where='arduino_rpc',
                                      only_in_packages=False)


setup(name='wheeler.arduino_rpc',
      version=version.getVersion(),
      description='Arduino RPC node packaged as Python package.',
      author='Christian Fobel',
      author_email='christian@fobel.net',
      url='http://github.com/wheeler-microfluidics/arduino_rpc.git',
      license='GPLv2',
      install_requires=['nadamq', 'path_helpers', 'clang_helpers>=0.2.post3'],
      packages=['arduino_rpc'],
      package_data=arduino_rpc_files)
