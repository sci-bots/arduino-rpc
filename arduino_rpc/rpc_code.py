from collections import OrderedDict

from protobuf_helpers import underscore_to_camelcase
from clang_helpers import (open_cpp_source, extract_class_declarations,
                           extract_method_signatures, get_stdint_type)
from clang_helpers.clang.cindex import Cursor, TypeKind
import itertools
import types
from cStringIO import StringIO
import pandas as pd
import numpy as np


def get_methods(rpc_header):
    root = open_cpp_source(rpc_header)
    node_class = extract_class_declarations(root)['Node']
    methods = extract_method_signatures(node_class)

    protobuf_methods = OrderedDict()

    def resolve_array_type(arg_type):
        declaration = arg_type.get_declaration()
        array_children = list(declaration.get_children())
        array_fields = OrderedDict([(c.displayname, c)
                                    for c in array_children if
                                    c.displayname])
        if not set(array_fields.keys()).difference(('length',
                                                    'data')):
            length_type = array_fields['length'].type.get_canonical().kind
            atom_type = (array_fields['data'].type.get_pointee()
                         .get_canonical().kind)
        return OrderedDict([('length_type', length_type),
                            ('atom_type', atom_type)])

    for method_name, signatures in methods.iteritems():
        if len(signatures) > 1:
            raise ValueError('Overloaded methods are currently not '
                             'supported, i.e., there must be at most one '
                             'signature for each method.')
        s = signatures[0]
        protobuf_methods[method_name] = OrderedDict()
        return_type = s['return_type'].get_canonical().kind
        if return_type == TypeKind.RECORD:
            return_type = resolve_array_type(s['return_type'])
        protobuf_methods[method_name]['return_type'] = return_type
        args = []
        for k, a in s['arguments'].iteritems():
            if isinstance(a, Cursor) and a.type.kind == TypeKind.RECORD:
                args.append((k, resolve_array_type(a.type)))
            else:
                args.append((k, a))
        protobuf_methods[method_name]['arguments'] = args
    return protobuf_methods


def get_command_processor_header_commands(methods):
    commands = []
    array_types = OrderedDict([
        ('int8_t', 'Int8Array'),
        ('int16_t', 'Int16Array'),
        ('int32_t', 'Int32Array'),
        ('uint8_t', 'UInt8Array'),
        ('uint16_t', 'UInt16Array'),
        ('uint32_t', 'UInt32Array'),
        ('float', 'FloatArray'),
    ])
    for name, type_info in methods.iteritems():
        return_type = get_stdint_type(type_info['return_type'])
        arguments = [[k, get_stdint_type(a)] for k, a in
                     type_info['arguments']]
        if return_type and return_type[1] == 'array':
            return_type += (array_types[return_type[0]], )
        for arg in arguments:
            if arg[1][1] == 'array':
                arg[1] += (array_types[arg[1][0]], )
        commands.append((underscore_to_camelcase(name), name, return_type,
                         arguments))
    return commands


def get_arg_info(arg_types):
    '''
    Return a `pandas.DataFrame` containing the name, number of dimensions, and
    `numpy`-dtype compatible atom type.

    Arguments
    ---------

     - `arg_types`: An iterable, where each entry is either a 2-tuple or 3-tuple.
       If an entry is a 2-tuple, it is assumed to be of the form `(<name>, <c type>)`.
       If an entry is a 3-tuple, it is assumed to be of the form
       `(<name>, (<atom c type>, ...)`.
    '''
    if not len(arg_types):
        return pd.DataFrame([])
    arg_info = pd.DataFrame([[v[0]] + ([0, v[1][:-2]] if isinstance(v[1], types.StringTypes)
                                       else [1, v[1][0][:-2]])
                             for v in arg_types], columns=['name', 'ndims', 'atom_type'])
    return arg_info


def get_struct_arg_info(arg_info, inplace=False):
    '''
    Add the following columns to the input `arg_info` frame:

     - `struct_types`: List of `(<name>, <atom_type>)` tuples.
     - `struct_field_size`: Total size of all struct types.

    Arguments
    ---------

     - `arg_info`: `pandas.DataFrame` in format returned by `get_arg_info`, i.e.,
       with the following columns:

           ['name', 'ndims', 'atom_type']
    '''
    if not inplace:
        arg_info = arg_info.copy()
    arg_info['struct_types'] = arg_info.apply(lambda x: [tuple(x[['name', 'atom_type']])]
                                              if x.ndims == 0 else
                                              [(x['name'] + '_length', 'uint16'),
                                               (x['name'] + '_data', 'uint16')], axis=1)
    arg_info['struct_field_size'] = arg_info.atom_type.map(lambda x: np.dtype(x).itemsize)
    arg_info.loc[arg_info.ndims > 0, 'struct_field_size'] = 2 * np.dtype('uint16').itemsize
    return arg_info


def payload_template(struct_arg_info):
    '''
    Return Python code to serialize arguments defined by `arg_info` frame.

    Arguments
    ---------

     - `struct_arg_info`: `pandas.DataFrame` in format returned by `get_struct_arg_info`,
       i.e., with the following columns:

           ['name', 'ndims', 'atom_type', 'struct_types', 'struct_field_size']
    '''
    if struct_arg_info.shape[0] == 0:
        return "payload_data == ''"

    out = StringIO()

    array_info = struct_arg_info.loc[struct_arg_info.ndims > 0]

    struct_size = struct_arg_info.struct_field_size.sum()
    arg_values = [[arg_i['name']] if arg_i.ndims == 0
                  else ["array_info.length['" + arg_i['name'] + "']",
                        "STRUCT_SIZE + array_info.start['" + arg_i['name'] + "']"]
                  for index, arg_i in struct_arg_info.iterrows()]
    print >> out, '''    STRUCT_SIZE = %s''' % struct_size
    print >> out, '\n'.join('    ' + array_info.name + ' = np.ascontiguousarray('
                            + array_info.name + ", dtype='" + array_info.atom_type + "')")
    if array_info.shape[0] > 0:
        print >> out, ('''    array_info = pd.DataFrame([{sizes}],\n'''
                       '''                               index=[{names}],\n'''
                       '''                               columns=['length'])'''
                       .format(sizes=', '.join(array_info.name + '.shape[0]'),
                               names=', '.join("'" + array_info.name + "'")))
        print >> out, '''    array_info['start'] = array_info.length.cumsum() - array_lengths.length'''
        print >> out, '''    array_data = ''.join([%s])''' % ', '.join(array_info.name + '.tostring()')
    else:
        print >> out, "    array_data = ''"
    print >> out, '''    payload_size = STRUCT_SIZE + len(array_data)'''

    print >> out, ('    struct_data = np.array([(%s, )],\n'
                   '                           dtype=%s)'
                   % (', '.join(list(itertools.chain(*arg_values))),
                      list(itertools.chain(*struct_arg_info.struct_types))))
    print >> out, '    payload_data = struct_data.tostring() + array_data'
    return out.getvalue()
