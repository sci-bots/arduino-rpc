import sys
from path_helpers import path

from ..rpc_data_frame import get_c_header_code, get_python_code
from ..code_gen import write_code


def parse_args(args=None):
    """Parses arguments, returns (options, args)."""
    from argparse import ArgumentParser

    if args is None:
        args = sys.argv

    parser = ArgumentParser(description='Generate code to interface with'
                            'methods of a Arduino C++ class.')
    action = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument('cpp_header', type=path, default=None)
    parser.add_argument('class_name', help='C++ class name to read methods '
                        'from.')
    parser.add_argument('-o', '--out_file', type=path, default='-')
    parser.add_argument('-f', '--force-overwrite', action='store_true')
    action.add_argument('--python', help='Generate Python code.',
                        action='store_true')
    action.add_argument('--cpp', help='Name for C++ command processor class '
                        'in underscore format (e.g., `my_class_name`)',
                        default=None)

    args = parser.parse_args()
    if args.out_file.isfile() and not args.force_overwrite:
        parser.error('Output file already exists.  Use `--force-overwrite` to '
                     'overwrite.')
    return args


if __name__ == '__main__':
    args = parse_args()

    if args.python:
        f_get_code = get_python_code
    else:
        f_get_code = lambda *args_: get_c_header_code(*(args_ + (args.cpp, )))

    write_code(args.cpp_header, args.class_name, args.out_file, f_get_code)
