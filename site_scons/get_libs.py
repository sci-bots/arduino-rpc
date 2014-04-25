import os
import sys

from SCons.Script import File

from path_helpers import path


def get_lib_paths():
    if sys.platform == 'win32':
        lib_paths = set(os.environ['PATH'].split(';'))
    else:
        lib_paths = set()
        if os.environ.has_key('LIBRARY_PATH'):
            lib_paths.update(os.environ['LIBRARY_PATH'].split(':'))
        if os.environ.has_key('LD_LIBRARY_PATH'):
            lib_paths.update(os.environ['LD_LIBRARY_PATH'].split(':'))
        lib_paths = (['/usr/lib', '/usr/lib/x86_64-linux-gnu',
                      '/usr/local/lib'] + list(lib_paths))
    return lib_paths


def get_lib(lib_name, LIBPATH=None):
    if not LIBPATH:
        LIBPATH = []
    else:
        LIBPATH = LIBPATH[:]
    LIBPATH += get_lib_paths()
    for lp in [path(p) for p in LIBPATH]:
        try:
            files = lp.files(lib_name)
        except OSError:
            continue
        if files:
            return File(sorted(files, key=len)[0])
    return None
