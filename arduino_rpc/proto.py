from collections import OrderedDict
from cStringIO import StringIO

import jinja2
from protobuf_helpers import underscore_to_camelcase
from clang_helpers import (open_cpp_source, extract_class_declarations,
                           extract_method_signatures)
from protobuf_helpers import CLANG_TYPE_KIND_TO_PROTOBUF_TYPE

from . import get_sketch_directory


def get_protobuf_methods():
    root = open_cpp_source(get_sketch_directory().joinpath('Node.h'))
    class_name, node_class = extract_class_declarations(root).items()[0]
    methods = extract_method_signatures(node_class)

    protobuf_methods = OrderedDict()

    for method_name, signatures in methods.iteritems():
        if len(signatures) > 1:
            raise ValueError('Overloaded methods are currently not supported, '
                             'i.e., there must be at most one signature for '
                             'each method.')
        s = signatures[0]
        protobuf_methods[method_name] = OrderedDict()
        protobuf_methods[method_name]['return_type'] = (
            CLANG_TYPE_KIND_TO_PROTOBUF_TYPE[s['return_type']])
        protobuf_methods[method_name]['arguments'] = (
            [(k, CLANG_TYPE_KIND_TO_PROTOBUF_TYPE[a])
             for k, a in s['arguments'].iteritems()])

    return protobuf_methods


def get_protobuf_definitions():
    protobuf_methods = get_protobuf_methods()

    command_type = '''
    enum CommandType {
    %s
    }''' % ('\n'.join(['  %-25s= %d;' % (v.upper(), i + 1)
                       for i, v in enumerate(protobuf_methods.keys())]))

    request_fields = ['  optional %sRequest %s = %d;' %
                      (underscore_to_camelcase(k), k, i + 1)
                      for i, (k, v) in enumerate(protobuf_methods.iteritems())]

    command_request = '''
    message CommandRequest {
    %s
    }''' % ('\n'.join(request_fields))

    response_fields = ['  optional %sResponse %s = %d;' %
                       (underscore_to_camelcase(k), k, i + 1)
                       for i, (k, v) in
                       enumerate(protobuf_methods.iteritems())]
    command_response = '''
    message CommandResponse {
    %s
    }''' % ('\n'.join(response_fields))

    output = StringIO()

    for k, v in protobuf_methods.iteritems():
        if v['arguments']:
            arguments = '\n%s\n' % '\n'.join(['  required %s %s = %d;' %
                                              (t, f, i + 1)
                                              for i, (f, t) in
                                              enumerate(v['arguments'])])
        else:
            arguments = ''
        print >> output, ('''message %sRequest {%s}''' %
                          (underscore_to_camelcase(k), arguments))

    for k, v in protobuf_methods.iteritems():
        if v['return_type'] is not None:
            return_type = ' required %s result = 1; ' % v['return_type']
        else:
            return_type = ''
        print >> output, ('''message %sResponse {%s}''' %
                          (underscore_to_camelcase(k), return_type))

    print >> output, command_type
    print >> output, ''
    print >> output, command_request
    print >> output, ''
    print >> output, command_response

    return output.getvalue()


COMMAND_PROCESSOR_TEMPLATE = r'''
#ifndef ___{{ class_name|upper }}_COMMAND_PROCESSOR___
#define ___{{ class_name|upper }}_COMMAND_PROCESSOR___

#include "UnionMessage.h"
#include "{{ pb_header }}"
#include "{{ class_name }}.h"


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
  {{ class_name }} &obj_;
public:
  CommandProcessor({{ class_name }} &obj) : obj_(obj) {}

  int process_command(uint16_t request_size, uint16_t buffer_size,
                      uint8_t *buffer) {
    /* ## Call operator ##
     *
     * Arguments:
     *
     *  - `request`: Protocol buffer command request structure,
     *  - `buffer_size`: The number of bytes in the arguments buffer.
     *  - `data`: The arguments buffer. */

    union { {% for camel_name, underscore_name, return_type, args in commands %}
      {{ camel_name }}Request {{ underscore_name }};
    {% endfor %} } request;

    union { {% for camel_name, underscore_name, return_type, args in commands %}
      {{ camel_name }}Response {{ underscore_name }};
    {% endfor %} } response;

    pb_field_t *fields_type;
    bool status = true;

    pb_istream_t istream = pb_istream_from_buffer(buffer, request_size);

    int request_type = decode_unionmessage_tag(&istream,
                                               CommandRequest_fields);

    /* Set the sub-request fields type based on the decoded message identifier
     * tag, which corresponds to a value in the `CommandType` enumerated type.
     */
    switch (request_type) { {% for camel_name, underscore_name, return_type, args in commands %}
      case CommandType_{{ underscore_name|upper }}:
        fields_type = (pb_field_t *){{ camel_name }}Request_fields;
        break;{% endfor %}
      default:
        status = false;
        break;
    }

    if (!status) { return -1; }

    /* Deserialize request according to the fields type determined above. */
    decode_unionmessage_contents(&istream, fields_type, &request);

    pb_ostream_t ostream = pb_ostream_from_buffer(buffer, buffer_size);

    /* Process the request, and populate response fields as necessary. */
    switch (request_type) { {% for camel_name, underscore_name, return_type, args in commands %}
      case CommandType_{{ underscore_name|upper }}:
        fields_type = (pb_field_t *){{ camel_name }}Response_fields;
        {% if return_type %}response.{{ underscore_name }}.result ={% endif %}
        obj_.{{ underscore_name }}({% for arg in args %}request.{{ underscore_name }}.{{ arg }}{% if not loop.last %}, {% endif %}{% endfor %});
        break;{% endfor %}
      default:
        return -1;
        break;
    }

    /* Serialize the response and write the encoded response to the buffer. */
    status = encode_unionmessage(&ostream, CommandResponse_fields, fields_type,
                                 &response);

    if (status) {
      return ostream.bytes_written;
    } else {
      return -1;
    }
  }
};

#endif  // #ifndef ___{{ class_name|upper }}_COMMAND_PROCESSOR___
'''


def get_command_processor_header():
    protobuf_methods = get_protobuf_methods()
    t = jinja2.Template(COMMAND_PROCESSOR_TEMPLATE)
    commands = []
    for underscore_name, details in protobuf_methods.iteritems():
        camel_name = underscore_to_camelcase(underscore_name)
        #if max([len(a[1]) for a in details['arguments']]) > 1:
            #continue
        argument_names = [a[0] for a in details['arguments']]
        commands.append((camel_name, underscore_name, details['return_type'],
                         argument_names))
    return t.render({'class_name': 'Node', 'commands': commands,
                     'pb_header': 'commands.pb.h'})
