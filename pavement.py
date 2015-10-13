from pprint import pprint
import sys

from paver.easy import task, needs, path, sh, cmdopts, options
from paver.setuputils import setup

sys.path.insert(0, '.')
from arduino_rpc.pavement_base import *
import version
import arduino_rpc


properties = dict(
      package_name='arduino_rpc',
      version=version.getVersion(),
      url='http://github.com/wheeler-microfluidics/arduino_rpc.git',
      short_description='Code generation for memory-efficient '
      'remote-procedure-calls between a host CPU (Python) and a device (C++) '
      '(e.g., Arduino).',
      long_description='The main features of this package include: 1) Extract '
      'method signatures from user-defined C++ class, 2) Assign a unique '
      '*"command code"* to each method, 3) Generate a `CommandProcessor<T>` '
      'C++ class, which calls appropriate method on instance of user type '
      'provided the corresponding serialized command array, and 4) Generate a '
      '`Proxy` Python class to call methods on remote device by serializing '
      'Python method call as command request and decoding command response '
      'from device as Python type(s).',
      category='Communication',
      author='Christian Fobel',
      author_email='christian@fobel.net')


options(
    rpc_module=arduino_rpc,
    LIB_PROPERTIES=properties,
    setup=dict(name=properties['package_name'].replace('_', '-'),
               description='\n'.join([properties['short_description'],
                                      properties['long_description']]),
               author_email=properties['author_email'],
               author=properties['author'],
               url=properties['url'],
               version=properties['version'],
               install_requires=['pandas>=0.15', 'nadamq>=0.7.post2',
                                 'path_helpers', 'clang_helpers>=0.3',
                                 'c-array-defs>=0.1.post2', 'arduino-memory'],
               # Install data listed in `MANIFEST.in`
               include_package_data=True,
               license='GPLv2',
               packages=[properties['package_name']]))


@task
@needs('generate_setup', 'minilib', 'setuptools.command.sdist')
def sdist():
    """Overrides sdist to make sure that our setup.py is generated."""
    pass
