from pprint import pprint
import sys

from paver.easy import task, needs, path, sh, cmdopts, options
from paver.setuputils import setup, find_package_data

import version
sys.path.append(path('.').abspath())
try:
    from arduino_rpc.proto import (CodeGenerator,
                                   generate_nanopb_code as
                                   _generate_nanopb_code,
                                   generate_pb_python_module as
                                   _generate_pb_python_module,
                                   generate_protobuf_definitions as
                                   _generate_protobuf_definitions,
                                   generate_rpc_buffer_header as
                                   _generate_rpc_buffer_header,
                                   generate_command_processor_header as
                                   _generate_command_processor_header)
except ImportError:
    import warnings

    warnings.warn('Could not import `clang`-based code-generator.')


arduino_rpc_files = find_package_data(package='arduino_rpc',
                                      where='arduino_rpc',
                                      only_in_packages=False)
#pprint(arduino_rpc_files)

PROTO_PREFIX = 'commands'

#DEFAULT_ARDUINO_BOARDS = ['uno', 'mega2560']
DEFAULT_ARDUINO_BOARDS = ['uno']

setup(name='wheeler.arduino_rpc',
      version=version.getVersion(),
      description='Arduino RPC node packaged as Python package.',
      author='Christian Fobel',
      author_email='christian@fobel.net',
      url='http://github.com/wheeler-microfluidics/arduino_rpc.git',
      license='GPLv2',
      install_requires=['arduino_scons', 'nadamq', 'path_helpers',
                        'arduino_helpers', 'nanopb_helpers', 'clang_helpers'],
      packages=['arduino_rpc'],
      package_data=arduino_rpc_files)


@task
def generate_protobuf_definitions():
    from arduino_rpc import get_sketch_directory, package_path

    protobuf_dir = package_path().joinpath('protobuf').abspath()
    _generate_protobuf_definitions(get_sketch_directory(), protobuf_dir)


@task
def generate_command_processor_header():
    from arduino_rpc import get_sketch_directory

    _generate_command_processor_header(get_sketch_directory(),
                                       get_sketch_directory())


@task
def generate_rpc_buffer_header():
    from arduino_rpc import get_sketch_directory

    _generate_rpc_buffer_header(get_sketch_directory())


@task
# Generate protocol buffer request and response definitions, implementing an
# RPC API using the union message pattern suggested in the [`nanopb`][1]
# examples.
#
# [1]: https://code.google.com/p/nanopb/source/browse/examples/using_union_messages/README.txt
@needs('generate_protobuf_definitions')
def generate_nanopb_code():
    from arduino_rpc import get_sketch_directory, package_path

    protobuf_dir = package_path().joinpath('protobuf').abspath()
    sketch = get_sketch_directory()
    _generate_nanopb_code(protobuf_dir, sketch)


@task
@needs('generate_protobuf_definitions')
def generate_pb_python_module():
    from arduino_rpc import package_path

    protobuf_dir = package_path().joinpath('protobuf').abspath()
    output_dir = package_path().abspath()
    _generate_pb_python_module(protobuf_dir, output_dir)


@task
@needs('generate_nanopb_code', 'generate_pb_python_module',
       'generate_rpc_buffer_header', 'generate_command_processor_header')
@cmdopts([('sconsflags=', 'f', 'Flags to pass to SCons.'),
          ('boards=', 'b', 'Comma-separated list of board names to compile '
           'for (e.g., `uno`).')])
def build_firmware():
    scons_flags = getattr(options, 'sconsflags', '')
    boards = [b.strip() for b in getattr(options, 'boards', '').split(',')
              if b.strip()]
    if not boards:
        boards = DEFAULT_ARDUINO_BOARDS
    for board in boards:
        # Compile firmware once for each specified board.
        sh('scons %s ARDUINO_BOARD="%s"' % (scons_flags, board))


@task
@needs('generate_setup', 'minilib', 'build_firmware',
       'setuptools.command.sdist')
def sdist():
    """Overrides sdist to make sure that our setup.py is generated."""
    pass
