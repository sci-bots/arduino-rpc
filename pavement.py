from pprint import pprint
import sys

from paver.easy import task, needs, path, sh, cmdopts, options
from paver.setuputils import setup, find_package_data

import version
sys.path.append(path('.').abspath())
import simple_rpc
from simple_rpc.proto import get_protobuf_definitions

simple_rpc_files = find_package_data(package='simple_rpc', where='simple_rpc',
                                     only_in_packages=False)
pprint(simple_rpc_files)

DEFAULT_ARDUINO_BOARDS = ['mega2560']

setup(name='wheeler.simple_rpc',
      version=version.getVersion(),
      description='Simple Arduino RPC node packaged as Python package.',
      author='Christian Fobel',
      author_email='christian@fobel.net',
      url='http://github.com/wheeler-microfluidics/simple_rpc.git',
      license='GPLv2',
      packages=['simple_rpc'],
      package_data=simple_rpc_files)


@task
def generate_protobuf_definitions():
    definition_str = get_protobuf_definitions()
    output_dir = path('simple_rpc').joinpath('protobuf').abspath()
    output_file = output_dir.joinpath('simple.proto')
    with output_file.open('wb') as output:
        output.write(definition_str)


@task
@needs('generate_protobuf_definitions')
def generate_nanopb_code():
    nanopb_home = path('simple_rpc').joinpath('libs', 'nanopb').abspath()
    output_dir = path('simple_rpc').joinpath('protobuf').abspath()
    sh('cd %s; ./protoc.sh %s simple.proto .' % (output_dir, nanopb_home))


@task
@needs('generate_nanopb_code')
def copy_nanopb_python_module():
    code_dir = path('simple_rpc').joinpath('protobuf', 'py').abspath()
    output_dir = path('simple_rpc').abspath()
    for f in code_dir.files('*.py'):
        f.copy(output_dir)


@task
@needs('copy_nanopb_python_module')
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
