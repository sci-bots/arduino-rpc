from collections import OrderedDict
from cStringIO import StringIO

import jinja2
from protobuf_helpers import underscore_to_camelcase
from clang_helpers import (open_cpp_source, extract_class_declarations,
                           extract_method_signatures)
from protobuf_helpers import CLANG_TYPE_KIND_TO_PROTOBUF_TYPE

from .template import COMMAND_PROCESSOR_TEMPLATE, COMMAND_PROTO_DEFINITIONS
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

    start_index = 10
    command_names = [(v, i + start_index) for i, v in
                     enumerate(protobuf_methods.keys())]
    command_types = [(underscore_to_camelcase(k), k, i + start_index)
                     for i, (k, v) in enumerate(protobuf_methods.iteritems())]
    commands = [(underscore_to_camelcase(k), k) + tuple(v.values())
                for k, v in protobuf_methods.iteritems()]

    t = jinja2.Template(COMMAND_PROTO_DEFINITIONS)
    return t.render(command_names=command_names, command_types=command_types,
                    commands=commands)


def get_command_processor_header():
    protobuf_methods = get_protobuf_methods()
    t = jinja2.Template(COMMAND_PROCESSOR_TEMPLATE)
    commands = [(underscore_to_camelcase(k), k) + tuple(v.values())
                for k, v in protobuf_methods.iteritems()]
    return t.render({'class_name': 'Node', 'commands': commands,
                     'pb_header': 'commands.pb.h'})
