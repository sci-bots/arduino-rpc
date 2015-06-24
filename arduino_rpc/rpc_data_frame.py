from collections import OrderedDict

import jinja2
import pandas as pd
import numpy as np
from .rpc_code import STD_ARRAY_TYPES
from . import get_sketch_directory


NP_STD_INT_TYPE = pd.Series(OrderedDict([
    ('bool', 'uint8'),
    ('int8_t', 'int8'),
    ('int8_t', 'int8'),
    ('uint8_t', 'uint8'),
    ('float', 'float32'),
    ('int32_t', 'int32'),
    ('int32_t', 'int32'),
    ('int64_t', 'int64'),
    ('int16_t', 'int16'),
    ('uint8_t', 'uint8'),
    ('uint32_t', 'uint32'),
    ('uint64_t', 'uint64'),
    ('uint16_t', 'uint16')]))


def get_c_header_code(df_sig_info, namespace):
    template = jinja2.Template(r'''
#ifndef ___{{ namespace.upper() }}___
#define ___{{ namespace.upper() }}___

#include "Array.h"
#include "remote_i2c_command.h"

namespace {{ namespace }} {

{% for (method_i, method_name, camel_name, arg_count), df_method_i in df_sig_info.groupby(['method_i', 'method_name', 'camel_name', 'arg_count']) %}
struct {{ camel_name }}Request {
{%- if arg_count > 0 %}
{{ '\n'.join('  ' + df_method_i.struct_atom_type + ' ' + df_method_i.arg_name + ';') }}
{%- endif %}
};

struct {{ camel_name }}Response {
{%- if df_method_i.return_atom_type.iloc[0] is not none %}
  {{ df_method_i.return_struct_atom_type.iloc[0] }} result;
{%- endif %}
};
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

{% for i, (method_i, method_name) in df_sig_info.drop_duplicates(subset='method_i')[['method_i', 'method_name']].iterrows() %}
    static const int CMD_{{ method_name.upper() }} = {{ '0x%02x' % method_i }};
{%- endfor %}

  UInt8Array process_command(uint16_t request_size, uint16_t buffer_size,
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
{% for (method_i, method_name, camel_name, arg_count), df_method_i in df_sig_info.groupby(['method_i', 'method_name', 'camel_name', 'arg_count']) %}
        case CMD_{{ method_name.upper() }}:
          {
            /* Cast buffer as request. */
            {{ camel_name }}Request &request = *(reinterpret_cast
                                          <{{ camel_name }}Request *>
                                          (&buffer[1]));
    {% if df_method_i.ndims.max() > 0 %}
            /* Add relative array data offsets to start payload structure. */
    {% for i, array_i in df_method_i[df_method_i.ndims > 0].iterrows() %}
            request.{{ array_i['arg_name'] }}.data = ({{ array_i.atom_type }} *)((uint8_t *)&request + (uint16_t)request.{{ array_i['arg_name'] }}.data);
    {%- endfor %}
    {%- endif -%}

    {%- if df_method_i.return_atom_type.iloc[0] is not none %}
            {{ camel_name }}Response response;

            response.result = {%- endif %}
            obj_.{{ method_name }}({% if arg_count > 0 %}{{ ', '.join('request.' + df_method_i.arg_name) }}{% endif %});
    {% if df_method_i.return_atom_type.iloc[0] is not none %}
            /* Copy result to output buffer. */
    {%- if df_method_i.return_ndims.iloc[0] > 0 %}
            /* Result type is an array, so need to do `memcpy` for array data. */
            uint16_t length = (response.result.length *
                               sizeof(response.result.data[0]));

            memcpy(&buffer[0], (uint8_t *)response.result.data, length);
            bytes_written += length;
    {%- else %}
            /* Cast start of buffer as reference of result type and assign result. */
            {{ camel_name }}Response &output = *(reinterpret_cast
                                                 <{{ camel_name }}Response *>
                                                 (&buffer[0]));
            output = response;
            bytes_written += sizeof(output);
    {%- endif %}
    {%- endif %}
          }
          break;
{% endfor %}
      default:
        bytes_written = -1;
    }
    UInt8Array result;
    if (bytes_written < 0) {
        result.length = 0xFFFF;
        result.data = NULL;
    } else {
        result.length = bytes_written;
        result.data = buffer;
    }
    return result;
  }
};

}  // namespace {{ namespace }}

#endif  // ifndef ___{{ namespace.upper() }}___
'''.strip())
    return template.render(df_sig_info=df_sig_info, namespace=namespace)


def get_python_code(df_sig_info):
    template = jinja2.Template(r'''
import pandas as pd
import numpy as np
from nadamq.NadaMq import cPacket, PACKET_TYPES
from arduino_rpc.proxy import ProxyBase


class Proxy(ProxyBase):

{% for i, (method_i, method_name) in df_sig_info.drop_duplicates(subset='method_i')[['method_i', 'method_name']].iterrows() %}
    _CMD_{{ method_name.upper() }} = {{ '0x%02x' % method_i }};
{%- endfor %}

{% for (method_i, method_name, camel_name, arg_count), df_method_i in df_sig_info.groupby(['method_i', 'method_name', 'camel_name', 'arg_count']) %}
    def {{ method_name }}(self{% if arg_count > 0 %}, {{ ', '.join(df_method_i.arg_name) }}{% endif %}):
        command = np.dtype('uint8').type(self._CMD_{{ method_name.upper() }})
{%- if arg_count > 0 %}
        ARG_STRUCT_SIZE = {{ df_method_i.struct_size.sum() }}
{%- if df_method_i.ndims.max() > 0 %}
{% for i, array_i in df_method_i[df_method_i.ndims > 0].iterrows() %}
        # Argument is an array, so cast to appropriate array type.
        {{ array_i['arg_name'] }} = np.ascontiguousarray({{ array_i['arg_name'] }}, dtype='{{ array_i.atom_np_type }}')
{%- endfor %}
        array_info = pd.DataFrame([
{%- for arg_name in df_method_i.loc[df_method_i.ndims > 0, 'arg_name'] -%}
        {{ arg_name }}.shape[0], {% endfor -%}],
                                  index=[
{%- for arg_name in df_method_i.loc[df_method_i.ndims > 0, 'arg_name'] -%}
        '{{ arg_name }}', {% endfor -%}],
                                  columns=['length'])
        array_info['start'] = array_info.length.cumsum() - array_info.length
        array_data = ''.join([
{%- for arg_name in df_method_i.loc[df_method_i.ndims > 0, 'arg_name'] -%}
        {{ arg_name }}.tostring(), {% endfor -%}])
{%- else %}
        array_data = ''
{%- endif %}
        payload_size = ARG_STRUCT_SIZE + len(array_data)
        struct_data = np.array([(
{%- for i, (arg_name, ndims, np_atom_type) in df_method_i[['arg_name', 'ndims', 'atom_np_type']].iterrows() -%}
{%- if ndims > 0 -%}
        array_info.length['{{ arg_name }}'], ARG_STRUCT_SIZE + array_info.start['{{ arg_name }}'], {% else -%}
        {{ arg_name }}, {% endif %}{% endfor %})],
                               dtype=[
{%- for i, (arg_name, ndims, np_atom_type) in df_method_i[['arg_name', 'ndims', 'atom_np_type']].iterrows() -%}
{%- if ndims > 0 -%}
        ('{{ arg_name }}_length', 'uint16'), ('{{ arg_name }}_data', 'uint16'), {% else -%}
        ('{{ arg_name }}', '{{ np_atom_type }}'), {% endif %}{% endfor %}])
        payload_data = struct_data.tostring() + array_data
{%- else %}
        payload_size = 0
        payload_data = ''
{%- endif %}

        payload_data = command.tostring() + payload_data
        packet = cPacket(data=payload_data, type_=PACKET_TYPES.DATA)
        response = self._send_command(packet)
{% if df_method_i.return_atom_type.iloc[0] is not none %}
        result = np.fromstring(response.data(), dtype='{{ df_method_i.return_atom_np_type.iloc[0] }}')
{% if df_method_i.return_ndims.iloc[0] > 0 %}
        # Return type is an array, so return entire array.
        return result
{% else %}
        # Return type is a scalar, so return first entry in array.
        return result[0]
{% endif %}{% endif %}
{% endfor %}
'''.strip())
    return template.render(df_sig_info=df_sig_info)


def get_struct_sig_info_frame(df_sig_info):
    df_sig_info = df_sig_info.copy()
    df_sig_info['struct_atom_type'] = df_sig_info.atom_type
    df_sig_info.loc[df_sig_info.ndims > 0, 'struct_atom_type'] = \
        STD_ARRAY_TYPES[df_sig_info.loc[df_sig_info.ndims > 0,
                                        'atom_type']].values
    df_sig_info['struct_size'] = 0

    df_sig_info.insert(4, 'return_atom_np_type', None)
    df_sig_info.loc[~df_sig_info.return_atom_type.isin([None]),
                    'return_atom_np_type'] = \
        NP_STD_INT_TYPE[df_sig_info.loc[~df_sig_info.return_atom_type
                                        .isin([None]),
                                        'return_atom_type']].values
    df_sig_info.insert(5, 'return_struct_atom_type',
                       df_sig_info['return_atom_type'])
    df_sig_info.loc[df_sig_info.return_ndims > 0, 'return_struct_atom_type'] = \
        STD_ARRAY_TYPES[df_sig_info.loc[df_sig_info.return_ndims > 0,
                                        'return_atom_type']].values

    df_sig_info.loc[df_sig_info.arg_count > 0, 'atom_np_type'] = \
        NP_STD_INT_TYPE[df_sig_info.loc[df_sig_info.arg_count > 0,
                                        'atom_type']].values
    df_sig_info.loc[df_sig_info.arg_count > 0, 'struct_size'] = \
        (df_sig_info.loc[df_sig_info.arg_count > 0,
                         'struct_atom_type']
         .map(lambda v: 2 * np.dtype('uint16').itemsize if v.endswith('Array')
              else np.dtype(NP_STD_INT_TYPE[v]).itemsize).values)
    return df_sig_info


def generate_rpc_buffer_header(output_dir, **kwargs):
    import warnings

    source_dir = kwargs.pop('source_dir', get_sketch_directory())
    template_filename = kwargs.get('template_filename', 'RPCBuffer.ht')

    default_settings = {'I2C_PACKET_SIZE': 32, 'PACKET_SIZE': 40,
                        'COMMAND_ARRAY_BUFFER_SIZE': 40,
                        'allocate_command_array_buffer': True,
                        'test': {'I2C_PACKET_SIZE': 124321}}
    board_settings = OrderedDict([
        ('uno', {'code': '__AVR_ATmega328P__', 'settings': default_settings}),
        ('mega2560', {'code': '__AVR_ATmega2560__',
                      'settings': dict(default_settings, PACKET_SIZE=256,
                                       COMMAND_ARRAY_BUFFER_SIZE=256)}),
        ('default', {'settings': default_settings})])

    kwargs.update({'board_settings': board_settings})

    template_file = source_dir.joinpath(template_filename)
    output_file = output_dir.joinpath(template_file.namebase + '.h')
    if output_file.isfile():
        warnings.warn('Skipping generation of buffer configuration since file '
                      'already exists: `%s`' % output_file)
    else:
        with output_file.open('wb') as output:
            t = jinja2.Template(template_file.bytes())
            output.write(t.render(**kwargs))
            print ('Wrote buffer configuration: `%s`' % output_file)
