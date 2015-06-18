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
import jinja2


header_template = jinja2.Template('''
#ifndef ___{{ header_name|upper }}___
#define ___{{ header_name|upper }}___

#include "Array.h"
#include "remote_i2c_command.h"

{% for i, case_i in df_c_sig_info.iterrows() %}
{{ case_i.arg_c_struct_def }}

{{ case_i.return_c_struct_def }}
{% endfor %}

template <typename Obj>
class CommandProcessor {
  /* # `CommandProcessor` #
   *
   * Each call to this functor processes a single command.
   *
   * All arguments are passed by reference, such that they may be used to form
   * a response.  If the integer return value of the call is zero, the call is
   * assumed to have no response required.  Otherwise, the arguments contain
   * must contain response values. */
protected:
  Obj &obj_;
public:
  CommandProcessor(Obj &obj) : obj_(obj) {}

{% for command_constant in command_constants %}
  {{ command_constant }}
{%- endfor %}

  int process_command(uint16_t request_size, uint16_t buffer_size,
                      uint8_t *buffer) {
    /* ## Call operator ##
     *
     * Arguments:
     *
     *  - `request`: Protocol buffer command request structure,
     *  - `buffer_size`: The number of bytes in the arguments buffer.
     *  - `data`: The arguments buffer. */
    uint8_t command = buffer[0];
    int bytes_read = 0;
    int bytes_written = 0;

    /* Set the sub-request fields type based on the decoded message identifier
     * tag, which corresponds to a value in the `CommandType` enumerated type.
     */
    switch (command) {
{% for i, case_i in df_c_sig_info.iterrows() %}
      case CMD_{{ case_i.underscore.upper() }}:
{{ case_i.case_code }}
          break;
{% endfor %}
      default:
        bytes_written = -1;
    }
    return bytes_written;
  }
};

#endif  // #ifndef ___{{ header_name|upper }}___
''')


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
        return "payload_data = ''"

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
        print >> out, '''    array_info['start'] = array_info.length.cumsum() - array_info.length'''
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


#########################################################
# Generate case code for single method signature.
def get_switch_case_tempate(sig_info):
    import jinja2

    arg_info = get_arg_info(sig_info.arg_types)
    context = sig_info.to_dict()
    if arg_info.shape[0] == 0:
        struct_arg_info = None
        context['array_info'] = None
        context['s'] = None
    else:
        struct_arg_info = get_struct_arg_info(arg_info)
        array_info = struct_arg_info[struct_arg_info.ndims > 0]
        context['start_offset'] = '\n'.join('  request.' + array_info.name + '.data = (uint8_t *)&request + (uint16_t)request.' + array_info.name + '.data;')
        context['args'] = ', '.join('request.' + struct_arg_info.name)
        context['array_info'] = array_info
        context['s'] = struct_arg_info
    context['has_args'] = struct_arg_info is not None
    context['has_arrays'] = context['array_info'] is not None

    context['signature'] = sig_info

    template = jinja2.Template(r'''
    {
      /* Cast buffer as request. */
      {{camel}}Request &request = *(reinterpret_cast
                                    <{{camel}}Request *>
                                    (&buffer[1]));
    {% if has_arrays %}
      /* Add relative array data offsets to start payload structure. */
    {% for i, info_i in array_info.iterrows() %}
      request.{{ info_i['name'] }}.data = ({{ info_i.atom_type }}_t *)((uint8_t *)&request + (uint16_t)request.{{ info_i['name'] }}.data);
    {%- endfor %}
    {%- endif -%}
    {%- if signature.return_type %}

      {{camel}}Response response;

      response.result = {%- endif %}
      obj_.{{underscore}}({% if has_args %}{{ ', '.join('request.' + s.name) }}{% endif %});

    {%- if signature.return_type %}

      /* Copy result to output buffer. */
    {%- if signature.return_dims == 0 %}
      /* Cast start of buffer as reference of result type and assign result. */
      {{camel}}Response &output = *(reinterpret_cast
                                   <{{camel}}Response *>
                                  (&buffer[0]));
      output = response;
      bytes_written += sizeof(output);
    {%- else %}
      /* Result type is an array, so need to do `memcpy` for array data. */
      uint16_t length = (response.result.length *
                         sizeof(response.result.data[0]));

      memcpy(&buffer[0], (uint8_t *)response.result.data, length);
      bytes_written += length;
    {% endif -%}
    {%- endif %}
    }
    ''')
    return template.render(**context)


array_types = pd.Series(OrderedDict([
    ('int8', 'Int8Array'),
    ('int16', 'Int16Array'),
    ('int32', 'Int32Array'),
    ('uint8', 'UInt8Array'),
    ('uint16', 'UInt16Array'),
    ('uint32', 'UInt32Array'),
    ('float32', 'FloatArray'),
]))


def get_arg_c_struct_def(signature, struct_arg_info):
    if struct_arg_info is None:
        fields = ''
    else:
        info = struct_arg_info.set_index('name')

        # For scalar types, the C type is directly inferred from the `atom_type`.
        info['c_type'] = info.atom_type + '_t'
        # For array types, the C type is the array struct type for the respective
        # `atom_type` (e.g., `UInt8Array`).
        info.loc[info.ndims > 0, 'c_type'] = array_types[info.loc[info.ndims > 0, 'atom_type']].values

        fields = '\n'.join('  ' + info.c_type + ' ' + info.index + ';')

    return '''
struct {name} {{
{fields}
}};
    '''.format(name=signature.camel + 'Request', fields=fields).strip()


def get_return_c_struct_def(signature):
    if signature.return_type is None:
        fields = ''
    elif isinstance(signature.return_type, types.StringTypes):
        fields = '  ' + signature.return_type + ' result;'
    else:
        fields = '  ' + signature.return_type[-1] + ' result;'
    return '''
struct {name} {{
{fields}
}};
    '''.format(name=signature.camel + 'Response', fields=fields).strip()


def get_signature_info(signature):
    '''
    Arguments
    ---------

     - `signature`: Signature in form returned by
       `get_command_processor_header_commands`.
    '''
    s = signature
    s['return_dims'] = 0 if isinstance(s.return_type, types.StringTypes) else 1
    s['return_atom_type'] = (s.return_type[:-2] if isinstance(s.return_type,
                                                              types.StringTypes)
                             else None if s.return_type is None
                             else s.return_type[0][:-2])
    return s


def get_py_command_constants(df_sig_info, starting_value=0x80):
    return ('_CMD_' + df_sig_info.underscore.str.upper() + ' = ' +
            df_sig_info.index.map(lambda x: hex(starting_value + x)))


def get_c_command_constants(df_sig_info, starting_value=0x80):
    return ('static const uint8_t CMD_' + df_sig_info.underscore.str.upper()
            + ' = ' + df_sig_info.index.map(lambda x: hex(starting_value + x))
            + ';')


def get_sig_info_frame(signatures):
    df_sig_info = pd.DataFrame(signatures, columns=['camel', 'underscore',
                                                    'return_type',
                                                    'arg_types'])
    df_sig_info = df_sig_info.apply(get_signature_info, axis=1)
    df_sig_info['arg_info'] = df_sig_info.arg_types.map(get_arg_info)
    df_sig_info['struct_arg_info'] = None
    df_sig_info['arg_count'] = df_sig_info.arg_info.map(lambda v: v.shape[0])
    df_sig_info.loc[df_sig_info.arg_count > 0, 'struct_arg_info'] =\
        df_sig_info.loc[df_sig_info.arg_count > 0,
                        'arg_info'].map(get_struct_arg_info)
    return df_sig_info


def get_c_sig_info_frame(df_sig_info):
    df_c_sig_info = df_sig_info.copy()
    df_c_sig_info['arg_c_struct_def'] = \
        df_c_sig_info.apply(lambda x: get_arg_c_struct_def(x,
                                                           x.struct_arg_info),
                            axis=1)
    df_c_sig_info['return_c_struct_def'] = \
        df_c_sig_info.apply(lambda x: get_return_c_struct_def(x), axis=1)
    df_c_sig_info['case_code'] = df_c_sig_info.apply(get_switch_case_tempate,
                                                     axis=1)
    return df_c_sig_info


def write_c_header(df_c_sig_info, header_path, header_name):
    with open(header_path, 'wb') as output:
        output.write(header_template
                     .render(header_name=header_name,
                             command_constants=get_c_command_constants(df_c_sig_info),
                             df_c_sig_info=df_c_sig_info))


def get_py_sig_info_frame(df_sig_info):
    df_py_sig_info = df_sig_info.copy()
    df_py_sig_info['payload_template'] = "    payload_data = ''"
    df_py_sig_info.loc[df_py_sig_info.arg_count > 0,
                       'payload_template'] = \
        (df_py_sig_info.loc[df_py_sig_info.arg_count > 0, 'struct_arg_info']
         .map(payload_template))
    df_py_sig_info['py_command_constant'] = \
        get_py_command_constants(df_py_sig_info)
    return df_py_sig_info


class_head = '''
import pandas as pd
import numpy as np
from nadamq.NadaMq import cPacket, cPacketParser, PACKET_TYPES


class ProxyBase(object):
    def __init__(self, serial):
        self._serial = serial

    def _send_command(self, packet):
        self._serial.write(packet.tostring())
        parser = cPacketParser()
        result = None

        while True:
            response = self._serial.read(self._serial.inWaiting())
            if response == '':
                continue
            result = parser.parse(np.fromstring(response, dtype='uint8'))
            if parser.message_completed:
                break
            elif parser.error:
                raise IOError('Error parsing.')
        return result
'''

template = jinja2.Template('''
class Proxy(ProxyBase):

{% for sig_info_i in df_py_sig_info.py_command_constant %}
{{ sig_info_i }}
{%- endfor %}

{% for i, sig_info_i in df_py_sig_info.iterrows() %}
def {{ sig_info_i.underscore }}(self{% if sig_info_i.arg_count >0 %}, {% endif %}{{ ', '.join(sig_info_i.arg_info.name) }}):
    command = np.dtype('uint8').type(self._CMD_{{ sig_info_i.underscore.upper() }})
{{ sig_info_i.payload_template }}
    payload_data = command.tostring() + payload_data
    packet = cPacket(data=payload_data, type_=PACKET_TYPES.DATA)
    response = self._send_command(packet)
    {% if sig_info_i.return_type is not none %}
    result = np.fromstring(response.data(), dtype='{{ sig_info_i.return_atom_type  }}')
    {% if sig_info_i.return_dims > 0 %}
    # Return type is an array, so return entire array.
    return result
    {% else %}
    # Return type is a scalar, so return first entry in array.
    return result[0]
    {% endif %}
    {% endif %}
{% endfor %}
'''.strip())


def python_code_template(df_py_sig_info):
    out = StringIO()

    print >> out, class_head
    print >> out, ''
    print >> out, '\n'.join(['    ' + v for v in
                             template.render(df_py_sig_info=df_py_sig_info)
                             .splitlines()]).strip()
    return out.getvalue()


def write_py_module(df_py_sig_info, module_path):
    with open(module_path, 'wb') as output:
        output.write(python_code_template(df_py_sig_info))
