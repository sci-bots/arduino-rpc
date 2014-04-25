from pprint import pprint
import sys

from paver.easy import task, needs, path, sh, cmdopts, options
from paver.setuputils import setup, find_package_data

import version
sys.path.append(path('.').abspath())
import blink

blink_files = find_package_data(package='blink', where='blink',
                                only_in_packages=False)
pprint(blink_files)

DEFAULT_ARDUINO_BOARDS = ['diecimila', 'uno', 'mega2560']

setup(name='wheeler.blink',
      version=version.getVersion(),
      description='Example Arduino sketch packaged as Python package.',
      author='Christian Fobel',
      author_email='christian@fobel.net',
      url='http://github.com/wheeler-microfluidics/blink.git',
      license='GPLv2',
      packages=['blink'],
      package_data=blink_files)


@task
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
