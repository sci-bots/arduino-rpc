from collections import OrderedDict

from path_helpers import path


def package_path():
    return path(__file__).parent


def get_sketch_directory():
    '''
    Return directory containing the `simple_rpc` Arduino sketch.
    '''
    return package_path().joinpath('Arduino', 'simple_rpc')


def get_nanopb_directory():
    return package_path().joinpath('libs', 'nanopb')


def get_nano_code_directory():
    return package_path().joinpath('protobuf', 'nano')


def get_includes():
    '''
    Return directories containing the `simple_rpc` Arduino header
    files.

    Modules that need to compile against `simple_rpc` should use this
    function to locate the appropriate include directories.

    Notes
    =====

    For example:

        import simple_rpc
        ...
        print ' '.join(['-I%s' % i for i in simple_rpc.get_includes()])
        ...

    '''
    return [get_sketch_directory(), get_nano_code_directory(),
            get_nanopb_directory()]


def get_sources():
    '''
    Return `simple_rpc` Arduino source file paths.

    Modules that need to compile against `simple_rpc` should use this
    function to locate the appropriate source files to compile.

    Notes
    =====

    For example:

        import simple_rpc
        ...
        print ' '.join(simple_rpc.get_sources())
        ...

    '''
    return (get_sketch_directory().files('*.c*') +
            get_nano_code_directory().files('*.c*') +
            get_nanopb_directory().files('*.c*'))


def get_firmwares():
    '''
    Return `simple_rpc` compiled Arduino hex file paths.

    This function may be used to locate firmware binaries that are available
    for flashing to [Arduino Uno][1] boards.

    [1]: http://arduino.cc/en/Main/arduinoBoardUno
    '''
    return OrderedDict([(board_dir.name, [f.abspath() for f in
                                          board_dir.walkfiles('*.hex')])
                        for board_dir in
                        package_path().joinpath('firmware').dirs()])
