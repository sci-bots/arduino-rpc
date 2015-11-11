# coding: utf-8
import re

import numpy as np
import pandas as pd
from google.protobuf.descriptor import FieldDescriptor


TYPE_CALLABLE_MAP = {
    FieldDescriptor.TYPE_DOUBLE: 'double',
    FieldDescriptor.TYPE_FLOAT: 'float',
    FieldDescriptor.TYPE_INT32: 'int32_t',
    FieldDescriptor.TYPE_INT64: 'int64_t',
    FieldDescriptor.TYPE_UINT32: 'uint32_t',
    FieldDescriptor.TYPE_UINT64: 'uint64_t',
    FieldDescriptor.TYPE_SINT32: 'int32_t',
    FieldDescriptor.TYPE_SINT64: 'int64_t',
    FieldDescriptor.TYPE_FIXED32: 'uint32_t',
    FieldDescriptor.TYPE_FIXED64: 'uint64_t',
    FieldDescriptor.TYPE_SFIXED32: 'int32_t',
    FieldDescriptor.TYPE_SFIXED64: 'int64_t',
    FieldDescriptor.TYPE_BOOL: 'bool',
    FieldDescriptor.TYPE_ENUM: 'int32_t'}


def get_protobuf_fields_frame(message_type):
    '''
    Return a `pandas.DataFrame` with one row per field/tag in the specified
    Protocol Buffers Python message type.

    Each row of the result data frame contains the following values:

      - `root_name`: Root Protocol Buffer message name.
      - `msg_name`: Protocol Buffer submessage name.
      - `msg_desc`: Protocol Buffer message descriptor instance.
      - `parent_name`: Name of the submessage in parent message ('' for top
        level tags).
      - `parent_field`: Protocol Buffer field descriptor of the submessage in
        parent message (`None` for top level tags).
      - `field_name`: Name of field/tag.
      - `field_desc`: Protocol Buffer field descriptor.
    '''
    frames = []

    def _frames(root, parent_field=None):
        atom_fields = [(n, f) for n, f in root.fields_by_name.iteritems()
                       if not f.type == f.TYPE_MESSAGE]
        if atom_fields:
            frame = pd.DataFrame(atom_fields,
                                columns=['field_name', 'field_desc'])
            frame.insert(0, 'msg_name', root.name)
            frame.insert(1, 'msg_desc', root)
            frame.insert(2, 'parent_name', parent_field.name
                         if parent_field else '')
            frame.insert(3, 'parent_field', parent_field)
            frame.insert(0, 'root_name', message_type.DESCRIPTOR.name)
            frames.append(frame)

        for n, f in root.fields_by_name.iteritems():
            if f.type == f.TYPE_MESSAGE:
                _frames(f.message_type, parent_field=f)

    _frames(message_type.DESCRIPTOR)
    return pd.concat(frames)


def extract_callback_data(df_protobuf, method_name):
    '''
    Return a (`pandas.DataFrame`, `pandas.Series`) tuple, corresponding to the
    parent message tags and the leaf field tag, respectively.

    Arguments
    ---------

     - `df_protobuf`: A `pandas.DataFrame` as returned by
       `get_protobuf_fields_frame` (one row per Protocol Buffer message field).
     - `method_name`: The method handler name, of the form
       `'on_<field1 name>[___<field2 name]>]_<signal>'`.


    Notes
    -----

    Each row of the parents data frame contains the following values:

      - `msg_name`: Protocol Buffer submessage name.
      - `msg_desc`: Protocol Buffer message descriptor instance.
      - `parent_name`: Name of the submessage in parent message ('' for top
        level tags).
      - `parent_field`: Protocol Buffer field descriptor of the submessage in
        parent message (`None` for top level tags).

    The leaf field series structure contains all of the fields from the
    `df_protobuf` columns, along with the following additional fields:

      - `atom_type`: Standard C-type corresponding to field data type.
      - `name`: Name of field in Protocol Buffer message.
    '''
    match = re.match(r'on_%s_(?P<fields>.+)_(?P<signal>[^_]+)' %
                     df_protobuf.iloc[0].root_name.lower(),
                     method_name).groupdict()
    fields = match['fields'].split('__')
    parents = [''] + fields[:-1]
    field = fields[-1]

    df_parents = (df_protobuf[df_protobuf.parent_name.isin(parents)]
                  [['msg_name', 'msg_desc', 'parent_name',
                    'parent_field']].drop_duplicates()
                  .set_index('parent_name'))
    df_parents = df_parents.loc[parents]

    s_field = df_protobuf[(df_protobuf.parent_name == parents[-1]) &
                          (df_protobuf.field_name == field)].iloc[0]
    s_field['atom_type'] = TYPE_CALLABLE_MAP[s_field.field_desc.type]
    s_field.name = field
    return df_parents, s_field


def get_field_value(root, field_descriptor, full_name, set_default=False):
    '''
    Extract field value from Protocol Buffer message `root`, based on the
    '.'-separated full field name.

    If the field is not set and `set_default=False`, return `nan`.
    If the field is an enumerated type, return name of value.
    '''
    parent = root

    level_fields = full_name.split('.')

    for level in level_fields[:-1]:
        if not set_default and not parent.HasField(level):
            return np.NaN
        parent = getattr(parent, level)
    level = level_fields[-1]
    if not set_default and not parent.HasField(level):
        return np.NaN
    value = getattr(parent, level)
    if field_descriptor.enum_type:
        return field_descriptor.enum_type.values_by_number[value].name
    else:
        return value


def resolve_field_values(message, set_default=False):
    '''
    Return a `pandas.DataFrame`, one row per Protocol Buffer atom field type
    (e.g., `uint32`, `bool`, etc.), indexed by parent message name.
    All fields related to the same parent can be accessed using:

        df_fields.loc[<parent_name>]

    The frame has the same columns as the frame returned from
    `arduino_rpc.protobuf.get_protobuf_fields_frame` with the addition of the following
    columns:

     - `full_name`: A '.'-separated fully-qualified field name relative to the root.
     - `value`: The value of the corresponding field in the supplied `message`.
    '''
    df_fields = get_protobuf_fields_frame(message)
    df_fields['full_name'] = (df_fields['parent_name'].map(lambda v: v + '.'
                                                           if v else '')
                              + df_fields['field_name'])
    df_fields['value'] = (df_fields[['field_desc', 'full_name']]
                          .apply(lambda v: get_field_value(message, *v.values,
                                                           set_default=set_default),
                                 axis=1))
    return df_fields.set_index('parent_name')
