from collections import OrderedDict

import nadamq
from path_helpers import path


def package_path():
    return path(__file__).parent


def get_sketch_directory():
    '''
    Return directory containing the Arduino sketch.
    '''
    return package_path().joinpath('Arduino').dirs()[0]


def get_nanopb_directory():
    return package_path().joinpath('libs', 'nanopb')


def get_nano_code_directory():
    return package_path().joinpath('protobuf', 'nano')


def get_includes():
    '''
    Return directories containing the Arduino header files.

    Notes
    =====

    For example:

        import arduino_rpc
        ...
        print ' '.join(['-I%s' % i for i in arduino_rpc.get_includes()])
        ...

    '''
    return [get_sketch_directory(), get_nano_code_directory(),
            get_nanopb_directory()] + nadamq.get_includes()


def get_sources():
    '''
    Return Arduino source file paths.  This includes any supplementary source
    files that are not contained in Arduino libraries.
    '''
    return (get_sketch_directory().files('*.c*') +
            get_nano_code_directory().files('*.c*') +
            get_nanopb_directory().files('*.c*') +
            nadamq.get_sources())


def get_firmwares():
    '''
    Return compiled Arduino hex file paths.

    This function may be used to locate firmware binaries that are available
    for flashing to [Arduino][1] boards.

    [1]: http://arduino.cc
    '''
    return OrderedDict([(board_dir.name, [f.abspath() for f in
                                          board_dir.walkfiles('*.hex')])
                        for board_dir in
                        package_path().joinpath('firmware').dirs()])
