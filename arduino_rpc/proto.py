import re
from collections import OrderedDict

import jinja2
from protobuf_helpers import underscore_to_camelcase, get_protobuf_type
from clang_helpers import (open_cpp_source, extract_class_declarations,
                           extract_method_signatures, get_stdint_type)
from clang_helpers.clang.cindex import Cursor, TypeKind

from .template import COMMAND_PROCESSOR_TEMPLATE, COMMAND_PROTO_DEFINITIONS


class CodeGenerator(object):
    command_processor_template = COMMAND_PROCESSOR_TEMPLATE
    command_proto_definitions = COMMAND_PROTO_DEFINITIONS

    def __init__(self, rpc_header, disable_i2c=False):
        self.rpc_header = rpc_header
        self.disable_i2c = disable_i2c

    def get_methods(self):
        root = open_cpp_source(self.rpc_header)
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

    def get_protobuf_methods(self):
        protobuf_methods = OrderedDict()
        for name, type_info in self.get_methods().iteritems():
            return_type = get_protobuf_type(type_info['return_type'])
            arguments = [(k, get_protobuf_type(a)) for k, a in
                         type_info['arguments']]
            protobuf_methods[name] = OrderedDict()
            protobuf_methods[name]['return_type'] = return_type
            protobuf_methods[name]['arguments'] = arguments
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

    def get_protobuf_definitions_context(self):
        protobuf_methods = self.get_protobuf_methods()

        start_index = 10
        command_names = [(v, i + start_index) for i, v in
                         enumerate(protobuf_methods.keys())]
        command_types = [(underscore_to_camelcase(k), k, i + start_index)
                         for i, (k, v) in
                         enumerate(protobuf_methods.iteritems())]
        commands = [(underscore_to_camelcase(k), k) + tuple(v.values())
                    for k, v in protobuf_methods.iteritems()]
        return command_names, command_types, commands

    def get_command_processor_header_commands(self):
        commands = []
        array_types = OrderedDict([
            ('uint8_t', 'UInt8Array'),
            ('uint16_t', 'UInt16Array'),
        ])
        for name, type_info in self.get_methods().iteritems():
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

    def get_command_processor_header(self, disable_i2c=None):
        if disable_i2c is None:
            disable_i2c = self.disable_i2c
        commands = self.get_command_processor_header_commands()
        t = jinja2.Template(self.command_processor_template)
        return t.render({'commands': commands, 'pb_header': 'commands.pb.h',
                         'disable_i2c': disable_i2c})
