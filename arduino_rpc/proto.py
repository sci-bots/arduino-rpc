from collections import OrderedDict
import warnings

import jinja2
from protobuf_helpers import underscore_to_camelcase, get_protobuf_type
from clang_helpers import (open_cpp_source, extract_class_declarations,
                           extract_method_signatures, get_stdint_type)
from clang_helpers.clang.cindex import Cursor, TypeKind
from nanopb_helpers import compile_nanopb, compile_pb

from . import get_sketch_directory
from .template import (COMMAND_PROCESSOR_TEMPLATE, COMMAND_PROTO_DEFINITIONS,
                       EXT_COMMAND_PROTO_DEFINITIONS,
                       EXT_MESSAGE_UNIONS_TEMPLATE)


class CodeGenerator(object):
    command_processor_template = COMMAND_PROCESSOR_TEMPLATE
    command_proto_definitions = COMMAND_PROTO_DEFINITIONS
    ext_message_unions_template = EXT_MESSAGE_UNIONS_TEMPLATE

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

    def get_protobuf_definitions(self, disable_i2c=None, template=None,
                                 extra_context=None):
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
        if template is None:
            template = self.command_proto_definitions
        context = dict(command_names=command_names,
                       command_types=command_types, commands=commands,
                       disable_i2c=disable_i2c)
        if extra_context is not None:
             context.update(extra_context)
        t = jinja2.Template(template)
        return t.render(context)

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
            ('int8_t', 'Int8Array'),
            ('int16_t', 'Int16Array'),
            ('int32_t', 'Int32Array'),
            ('uint8_t', 'UInt8Array'),
            ('uint16_t', 'UInt16Array'),
            ('uint32_t', 'UInt32Array'),
            ('float', 'FloatArray'),
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
        return t.render({'commands': commands, 'pb_header': 'commands_pb.h',
                         'disable_i2c': disable_i2c})

    def get_ext_message_unions_header(self, project_prefix):
        commands = self.get_command_processor_header_commands()
        t = jinja2.Template(self.ext_message_unions_template)
        return t.render({'commands': commands,
                         'project_prefix': project_prefix,
                         'camel_project_prefix':
                         underscore_to_camelcase(project_prefix)})


def generate_nanopb_code(source_dir, destination_dir):
    for proto_path in source_dir.files('*.proto'):
        prefix = proto_path.namebase
        options_path = proto_path.parent.joinpath(proto_path.namebase +
                                                  '.options')
        if options_path.isfile():
            nanopb = compile_nanopb(proto_path, options_path)
        else:
            nanopb = compile_nanopb(proto_path)
        header_name = prefix + '_pb.h'
        source_name = prefix + '_pb.c'
        destination_dir.joinpath(header_name).write_bytes(nanopb['header'])
        destination_dir.joinpath(source_name).write_bytes(
            nanopb['source'].replace('{{ header_path }}', header_name))


def generate_pb_python_module(source_dir, destination_dir):
    for proto_path in source_dir.files('*.proto'):
        prefix = proto_path.namebase
        pb = compile_pb(proto_path)
        destination_dir.joinpath('protobuf_%s.py' %
                                 prefix).write_bytes(pb['python'])


def generate_protobuf_definitions(source_dir, output_dir,
                                  protobuf_prefix='commands', template=None,
                                  extra_context=None):
    code_generator = CodeGenerator(source_dir.joinpath('Node.h'))
    definition_str = code_generator.get_protobuf_definitions(template=template,
                                                             extra_context=
                                                             extra_context)
    output_file = output_dir.joinpath('%s.proto' % protobuf_prefix)
    with output_file.open('wb') as output:
        output.write(definition_str)


def generate_ext_protobuf_definitions(project_prefix, source_dir, output_dir,
                                      protobuf_prefix='ext_commands'):
    generate_protobuf_definitions(source_dir, output_dir,
                                  project_prefix + '_commands',
                                  template=EXT_COMMAND_PROTO_DEFINITIONS,
                                  extra_context={'camel_project_prefix':
                                                 underscore_to_camelcase(
                                                     project_prefix),
                                                 'project_prefix':
                                                 project_prefix})


def generate_ext_message_unions_header(project_prefix, source_dir,
                                       output_path):
    code_generator = CodeGenerator(source_dir.joinpath('Node.h'))
    header_str = code_generator.get_ext_message_unions_header(project_prefix)
    with output_path.open('wb') as output:
        output.write(header_str)


def generate_command_processor_header(source_dir, output_dir):
    code_generator = CodeGenerator(source_dir.joinpath('Node.h'))
    header_str = code_generator.get_command_processor_header()
    output_file = output_dir.joinpath('NodeCommandProcessor.h')
    with output_file.open('wb') as output:
        output.write(header_str)


def generate_rpc_buffer_header(output_dir, **kwargs):
    source_dir = kwargs.pop('source_dir', get_sketch_directory())
    template_filename = kwargs.get('template_filename', 'RPCBuffer.ht')

    default_settings = {'I2C_PACKET_SIZE': 32, 'PACKET_SIZE': 40,
                        'COMMAND_ARRAY_BUFFER_SIZE': 40,
                        'allocate_command_array_buffer': True,
                        'test': {'I2C_PACKET_SIZE': 124321}}
    board_settings = OrderedDict([
        ('uno', {'code': '__AVR_ATmega3280__', 'settings': default_settings}),
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
