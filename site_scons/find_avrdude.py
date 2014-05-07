import re
import sys
from sys import platform as _platform
import os
from itertools import chain

from path_helpers import path

home_dir = path('~').expand()

ARDUINO_SEARCH_PATHS = [home_dir, ]
if _platform == 'win32':
    from win32com.shell import shell, shellcon
    mydocs = shell.SHGetFolderPath(0, shellcon.CSIDL_PERSONAL, 0, 0)
    AVRDUDE_NAME = 'avrdude.exe'
    ARDUINO_SEARCH_PATHS += [path(mydocs), path('%SYSTEMDRIVE%/').expand(),
                             path('%PROGRAMFILES%').expand(), ]
elif _platform == 'darwin':
    AVRDUDE_NAME = 'avrdude'
    ARDUINO_SEARCH_PATHS += [path('/Applications/Arduino.app/Contents/'
                                  'Resources/Java')]
else:
    AVRDUDE_NAME = 'avrdude'
    ARDUINO_SEARCH_PATHS += [path("/usr/share/")]


def get_arduino_paths():
    fs = []
    for p in ARDUINO_SEARCH_PATHS:
        fs += get_avrdude_list(p)

    if not fs:
        print >> sys.stderr, '''\
    ERROR: arduino install directory not found!

    Searched:
        %s''' % '\n    '.join(ARDUINO_SEARCH_PATHS)
        sys.exit(1)

    if os.name == 'nt':
        # use arduino version 0023 if it exists
        for avrdude in fs:
            if get_arduino_version(avrdude) == '0023':
                break
    else:
        avrdude = fs[0]

    p = avrdude.parent
    while p and p.name != 'hardware':
        p = p.parent
    if not p:
        print >> sys.stderr, '''Arduino install path not found.'''
        sys.exit(1)
    arduino_path = p.parent
    avrdude_conf = list(arduino_path.walkfiles('avrdude.conf'))
    if not avrdude_conf:
        print >> sys.stderr, ('avrdude configuration `avrdude.conf` path not '
                              'found.')
        sys.exit(1)
    else:
        avrdude_conf = avrdude_conf[0]
    return arduino_path, avrdude, avrdude_conf


def get_avrdude_list(p):
    return list(set(chain(*[d.walkfiles(AVRDUDE_NAME)
                            for d in p.dirs('arduino*')])))


def get_arduino_version(p):
    while p and not (p / path('revisions.txt')).exists():
        p = p.parent
    if not p:
        print >> sys.stderr, '''Arduino install path not found.'''
        sys.exit(1)
    with open(p / path('revisions.txt'), 'r') as f:
        version = f.readline()
    f.close()
    match = re.search(r'ARDUINO (.*) - .*', version)
    if match:
        return match.groups()[0]
    else:
        return None


if __name__ == '__main__':
    arduino_path, avrdude, avrdude_conf = get_arduino_paths()
    print 'found arduino path:', arduino_path
    print 'using newest avrdude:', avrdude
    print 'using avrdude config:', avrdude_conf
