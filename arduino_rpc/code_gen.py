import sys

from clang_helpers import open_cpp_source, extract_class_declarations
from clang_helpers.data_frame import get_clang_methods_frame
from .rpc_data_frame import get_struct_sig_info_frame


def write_code(cpp_header, class_name, out_file, f_get_code):
    root = open_cpp_source(cpp_header)
    node_class = extract_class_declarations(root)[class_name]

    df_sig_info = get_clang_methods_frame(node_class, std_types=True)
    df_sig_info.head()

    df_struct_sig_info = get_struct_sig_info_frame(df_sig_info)
    df_struct_sig_info.method_i += 0x80

    if out_file == '-':
        # Write code to `stdout`.
        output = sys.stdout
    else:
        output = out_file.open('wb')

    try:
        print >> output, f_get_code(df_struct_sig_info)
    finally:
        output.close()
