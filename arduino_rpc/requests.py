from collections import OrderedDict

from .protobuf_commands import *


try:
    eval('CommandType')
except NameError:
    # `protobuf_commands.py` must have been generated with an old version of
    # `protoc`, so we have to manually wrap the `_COMMANDTYPE` enum.
    from .protobuf_commands import _COMMANDTYPE

    class CommandType(object):
        by_name = OrderedDict(sorted(_COMMANDTYPE.values_by_number.items()))
        by_value = OrderedDict([(v, k) for k, v in by_name.items()])

        def Name(self, value):
            return self.by_value[value]

        def Value(self, name):
            return self.by_name[name]


# Collect the names of all request types.
REQUEST_TYPES = OrderedDict([(k[:-len('Request')], eval(k))
                             for k in locals().keys()
                             if k != 'CommandRequest' and
                             k.endswith('Request')])


__all__ = ['REQUEST_TYPES', 'CommandRequest', 'CommandResponse', 'CommandType']
