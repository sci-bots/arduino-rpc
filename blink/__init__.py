from path_helpers import path


def package_path():
    return path(__file__).parent


def get_sketch_directory():
    '''
    Return directory containing the `blink` Arduino sketch.
    '''
    return package_path().joinpath('Arduino', 'blink')


def get_includes():
    '''
    Return directories containing the `blink` Arduino header
    files.

    Modules that need to compile against `blink` should use this
    function to locate the appropriate include directories.

    Notes
    =====

    For example:

        import blink
        ...
        print ' '.join(['-I%s' % i for i in blink.get_includes()])
        ...

    '''
    return get_sketch_directory()


def get_sources():
    '''
    Return `blink` Arduino source file paths.

    Modules that need to compile against `blink` should use this
    function to locate the appropriate source files to compile.

    Notes
    =====

    For example:

        import blink
        ...
        print ' '.join(blink.get_sources())
        ...

    '''
    return get_sketch_directory().files('*.c*')


def get_firmwares():
    '''
    Return `blink` compiled Arduino hex file paths.

    This function may be used to locate firmware binaries that are available
    for flashing to [Arduino Uno][1] boards.

    [1]: http://arduino.cc/en/Main/arduinoBoardUno
    '''
    return [f.abspath() for f in
            package_path().joinpath('firmware').walkfiles('*.hex')]
