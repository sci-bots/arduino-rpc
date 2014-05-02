from collections import OrderedDict
from cStringIO import StringIO

from protobuf_helpers import underscore_to_camelcase
from clang_helpers import (open_cpp_source, extract_class_declarations,
                           extract_method_signatures)
from protobuf_helpers import CLANG_TYPE_KIND_TO_PROTOBUF_TYPE

from . import get_sketch_directory


def get_protobuf_definitions():
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

    command_type = '''
    enum CommandType {
    %s
    }''' % ('\n'.join(['  %-25s= %d;' % (v.upper(), i + 2)
                       for i, v in enumerate(protobuf_methods.keys())]))

    request_fields = ['  optional %sRequest %s = %d;' %
                      (underscore_to_camelcase(k), k, i + 2)
                      for i, (k, v) in enumerate(protobuf_methods.iteritems())]

    command_request = '''
    message CommandRequest {
    // Identifies which field is filled in.
    required CommandType type = 1;
    %s
    }''' % ('\n'.join(request_fields))

    response_fields = ['  optional %sResponse %s = %d;' %
                       (underscore_to_camelcase(k), k, i + 2)
                       for i, (k, v) in
                       enumerate(protobuf_methods.iteritems())]
    command_response = '''
    message CommandResponse {
    // Identifies which field is filled in.
    required CommandType type = 1;
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
