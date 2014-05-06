from collections import OrderedDict

import jinja2
from protobuf_helpers import (underscore_to_camelcase,
                              CLANG_TYPE_KIND_TO_PROTOBUF_TYPE)
from clang_helpers import (open_cpp_source, extract_class_declarations,
                           extract_method_signatures)

from .template import COMMAND_PROCESSOR_TEMPLATE, COMMAND_PROTO_DEFINITIONS


class CodeGenerator(object):
    command_processor_template = COMMAND_PROCESSOR_TEMPLATE
    command_proto_definitions = COMMAND_PROTO_DEFINITIONS

    def __init__(self, rpc_header, disable_i2c=False):
        self.rpc_header = rpc_header
        self.disable_i2c = disable_i2c

    def get_protobuf_methods(self):
        root = open_cpp_source(self.rpc_header)
        class_name, node_class = extract_class_declarations(root).items()[0]
        methods = extract_method_signatures(node_class)

        protobuf_methods = OrderedDict()

        for method_name, signatures in methods.iteritems():
            if len(signatures) > 1:
                raise ValueError('Overloaded methods are currently not '
                                 'supported, i.e., there must be at most one '
                                 'signature for each method.')
            s = signatures[0]
            protobuf_methods[method_name] = OrderedDict()
            protobuf_methods[method_name]['return_type'] = (
                CLANG_TYPE_KIND_TO_PROTOBUF_TYPE[s['return_type']])
            protobuf_methods[method_name]['arguments'] = (
                [(k, CLANG_TYPE_KIND_TO_PROTOBUF_TYPE[a])
                 for k, a in s['arguments'].iteritems()])
        return protobuf_methods

    def get_protobuf_definitions(self, disable_i2c=None):
        if disable_i2c is None:
            disable_i2c = self.disable_i2c
        protobuf_methods = self.get_protobuf_methods()

        start_index = 10
        command_names = [(v, i + start_index) for i, v in
                         enumerate(protobuf_methods.keys())]
        command_types = [(underscore_to_camelcase(k), k, i + start_index)
                         for i, (k, v) in
                         enumerate(protobuf_methods.iteritems())]
        commands = [(underscore_to_camelcase(k), k) + tuple(v.values())
                    for k, v in protobuf_methods.iteritems()]

        t = jinja2.Template(self.command_proto_definitions)
        return t.render(command_names=command_names,
                        command_types=command_types, commands=commands,
                        disable_i2c=disable_i2c)

    def get_command_processor_header(self, disable_i2c=None):
        if disable_i2c is None:
            disable_i2c = self.disable_i2c
        protobuf_methods = self.get_protobuf_methods()
        t = jinja2.Template(self.command_processor_template)
        commands = [(underscore_to_camelcase(k), k) + tuple(v.values())
                    for k, v in protobuf_methods.iteritems()]
        return t.render({'commands': commands, 'pb_header': 'commands.pb.h',
                         'disable_i2c': disable_i2c})
