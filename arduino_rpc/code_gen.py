import sys
import types

from path_helpers import path
import pandas as pd
from clang_helpers import open_cpp_source, extract_class_declarations
from clang_helpers.data_frame import get_clang_methods_frame
from .rpc_data_frame import get_struct_sig_info_frame


def get_multilevel_method_sig_frame(cpp_header, class_name, *args, **kwargs):
    '''
    Given one or more C++ header paths, each with a corresponding C++ class
    name, return a `pandas.DataFrame` with one row per method argument.


    Notes
    -----

     - Each row in the frame has a `class_name` (including namespace) and
       `method_name`, indicating the specific method that corresponds to the
       row argument.
     - Template classes are supported.  For example, the class defined as:

           class ClassName<typename Parameter1, typename Parameter2> {...};

       is referenced in the frame with the `class_name` of
       `ClassName<Parameter1, Parameter2>`.
     - Only rows corresponding to the *last* occurrence of each method name are
       included in the data frame.  The order is determined by the order of the
       headers and classes provided in the `cpp_header` argument and the
       `class_name` argument, respectively.
    '''
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
        frame.insert(1, 'class_name', class_)
        frames.append(frame)

    df_struct_sig_info = pd.concat(frames).reset_index(drop=True)

    # Method names may occur in multiple headers.  Only process the last
    # occurrence in the table for each method.
    df_last_i = (df_struct_sig_info.loc[(df_struct_sig_info.arg_count == 0) |
                                        (df_struct_sig_info.arg_i == 0)]
                .reset_index().groupby('method_name').nth(-1)['index'])
    df_struct_sig_info['index_0'] = (df_struct_sig_info.reset_index()
                                    .groupby(['class_name',
                                              'method_name'])['index']
                                    .transform(lambda x: x.iloc[0]))
    df_unique_methods = df_struct_sig_info[df_struct_sig_info.index_0 ==
                                           df_last_i[df_struct_sig_info
                                                     .method_name]].copy()

    class_i = pd.Series(df_unique_methods.class_name.unique())
    class_i = pd.Series(class_i.index, index=class_i)
    df_unique_methods.method_i += 0x20 * class_i[df_unique_methods
                                                 .class_name].values
    return df_unique_methods


def write_code(cpp_header, class_name, out_file, f_get_code, *args, **kwargs):
    '''
    Provided a list of C++ header files and a list of class names to discover
    in the corresponding files, write the result of the provided `f_get_code`
    function to the supplied output file path.

    Method signatures are found using the `get_multilevel_method_sig_frame`
    function (see function docstring for more details).

    Note that for methods with the same name, only the last discovered method
    (according to the order in the `class_name` list) will be included in the

    Arguments
    ---------

     - `cpp_header`: A single filepath to a C++ header, or a list of header
       paths.
     - `class_name`: A single C++ class name (including namespace), or a list
       of class names.
       * Template classes are supported.  For example, the class defined as:

             class ClassName<typename Parameter1, typename Parameter2> {...};

         is referenced in the frame with the `class_name` of
         `ClassName<Parameter1,Parameter2>`.
    '''
    methods_filter = kwargs.pop('methods_filter', lambda x: x)

    # Apply filter to methods (accepts all rows by default).
    df_methods = methods_filter(get_multilevel_method_sig_frame(cpp_header,
                                                                class_name,
                                                                *args,
                                                                **kwargs))

    if out_file == '-':
        # Write code to `stdout`.
        output = sys.stdout
    else:
        output = out_file.open('wb')

    try:
        print >> output, f_get_code(df_methods)
    finally:
        output.close()
