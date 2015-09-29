from collections import OrderedDict

from path_helpers import path


def package_path():
    return path(__file__).parent


def get_library_directory():
    '''
    Return directory containing the Arduino library headers.
    '''
    return package_path().joinpath('Arduino', 'library')


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
    import nanopb_helpers
    import nadamq
    import c_array_defs
    import arduino_memory

    includes = ([get_library_directory()] +
                nanopb_helpers.get_includes() + nadamq.get_includes() +
                arduino_memory.get_includes() + c_array_defs.get_includes())
    return includes


def get_sources():
    '''
    Return Arduino source file paths.  This includes any supplementary source
    files that are not contained in Arduino libraries.
    '''
    import nanopb_helpers
    import nadamq

    return nadamq.get_sources() + nanopb_helpers.get_sources()


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
