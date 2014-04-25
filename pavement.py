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
@cmdopts([('sconsflags=', 'f', 'Flags to pass to SCons.')])
def build_firmware():
    sh('scons %s' % getattr(options, 'sconsflags', ''))


@task
@needs('generate_setup', 'minilib', 'build_firmware',
       'setuptools.command.sdist')
def sdist():
    """Overrides sdist to make sure that our setup.py is generated."""
    pass
