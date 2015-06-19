import sys
import types

from path_helpers import path
import pandas as pd
from clang_helpers import open_cpp_source, extract_class_declarations
from clang_helpers.data_frame import get_clang_methods_frame
from .rpc_data_frame import get_struct_sig_info_frame


def write_code(cpp_header, class_name, out_file, f_get_code, *args, **kwargs):
    if isinstance(cpp_header, types.StringTypes):
        cpp_header = [cpp_header]
    if isinstance(class_name, types.StringTypes):
        class_name = [class_name]
    assert(len(cpp_header) == len(class_name))

    frames = []
    for header, class_ in zip(cpp_header, class_name):
        root = open_cpp_source(header, *args, **kwargs)
        node_class = extract_class_declarations(root)[class_]

        df_sig_info = get_clang_methods_frame(node_class, std_types=True)

        frame = get_struct_sig_info_frame(df_sig_info)
        frame.insert(0, 'header_name', path(header).name)
        frames.append(frame)

    df_struct_sig_info = pd.concat(frames)

    header_i = pd.Series(df_struct_sig_info.header_name.unique())
    header_i = pd.Series(header_i.index, index=header_i)
    df_struct_sig_info.method_i += 0x30 * header_i[df_struct_sig_info
                                                   .header_name].values


    if out_file == '-':
        # Write code to `stdout`.
        output = sys.stdout
    else:
        output = out_file.open('wb')

    try:
        print >> output, f_get_code(df_struct_sig_info)
    finally:
        output.close()
