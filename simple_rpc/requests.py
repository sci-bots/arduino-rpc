from collections import OrderedDict

from simple_pb2 import *


# Collect the names of all request types.
REQUEST_TYPES = OrderedDict([(k[:-len('Request')], eval(k)())
                             for k in locals().keys()
                             if k != 'CommandRequest' and
                             k.endswith('Request')])


__all__ = ['REQUEST_TYPES', 'CommandRequest', 'CommandResponse', 'CommandType']
