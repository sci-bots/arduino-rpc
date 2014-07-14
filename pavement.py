from pprint import pprint
import sys

from paver.easy import task, needs, path, sh, cmdopts, options
from paver.setuputils import setup, find_package_data

import version
sys.path.append(path('.').abspath())
try:
    from arduino_rpc.proto import CodeGenerator
except ImportError:
    import warnings

    warnings.warn('Could not import `clang`-based code-generator.')


arduino_rpc_files = find_package_data(package='arduino_rpc',
                                      where='arduino_rpc',
                                      only_in_packages=False)
pprint(arduino_rpc_files)

PROTO_PREFIX = 'commands'

DEFAULT_ARDUINO_BOARDS = ['uno', 'mega2560']

setup(name='wheeler.arduino_rpc',
      version=version.getVersion(),
      description='Arduino RPC node packaged as Python package.',
      author='Christian Fobel',
      author_email='christian@fobel.net',
      url='http://github.com/wheeler-microfluidics/arduino_rpc.git',
      license='GPLv2',
      install_requires=['nadamq', 'path_helpers', 'bitarray',
                        'arduino_helpers', 'clang_helpers'],
      packages=['arduino_rpc'],
      package_data=arduino_rpc_files)


@task
def generate_protobuf_definitions():
    from arduino_rpc import get_sketch_directory, package_path

    code_generator = CodeGenerator(get_sketch_directory().joinpath('Node.h'))
    definition_str = code_generator.get_protobuf_definitions()
    output_dir = package_path().joinpath('protobuf').abspath()
    output_file = output_dir.joinpath('%s.proto' % PROTO_PREFIX)
    with output_file.open('wb') as output:
        output.write(definition_str)


@task
def generate_command_processor_header():
    from arduino_rpc import get_sketch_directory

    code_generator = CodeGenerator(get_sketch_directory().joinpath('Node.h'))
    header_str = code_generator.get_command_processor_header()
    output_dir = get_sketch_directory()
    output_file = output_dir.joinpath('NodeCommandProcessor.h')
    with output_file.open('wb') as output:
        output.write(header_str)


@task
# Generate protocol buffer request and response definitions, implementing an
# RPC API using the union message pattern suggested in the [`nanopb`][1]
# examples.
#
# [1]: https://code.google.com/p/nanopb/source/browse/examples/using_union_messages/README.txt
@needs('generate_protobuf_definitions')
def generate_nanopb_code():
    from arduino_rpc import package_path

    nanopb_home = package_path().joinpath('libs', 'nanopb').abspath()
    output_dir = package_path().joinpath('protobuf').abspath()
    sh('cd %s; ./protoc.sh %s %s.proto .' % (output_dir, nanopb_home,
                                             PROTO_PREFIX))


@task
@needs('generate_nanopb_code')
def copy_nanopb_python_module():
    from arduino_rpc import package_path

    code_dir = package_path().joinpath('protobuf', 'py').abspath()
    output_dir = package_path().abspath()
    protobuf_commands_file = list(code_dir.files('*_pb2.py'))[0]
    protobuf_commands_file.copy(output_dir.joinpath('protobuf_commands.py'))


@task
@needs('copy_nanopb_python_module', 'generate_command_processor_header')
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
