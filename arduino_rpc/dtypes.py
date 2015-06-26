from collections import OrderedDict

import pandas as pd


STD_ARRAY_TYPES = pd.Series(OrderedDict([
    ('int8_t', 'Int8Array'),
    ('int16_t', 'Int16Array'),
    ('int32_t', 'Int32Array'),
    ('uint8_t', 'UInt8Array'),
    ('uint16_t', 'UInt16Array'),
    ('uint32_t', 'UInt32Array'),
    ('float', 'FloatArray'),
]))


NP_ARRAY_TYPES = pd.Series(OrderedDict([
    ('int8', 'Int8Array'),
    ('int16', 'Int16Array'),
    ('int32', 'Int32Array'),
    ('uint8', 'UInt8Array'),
    ('uint16', 'UInt16Array'),
    ('uint32', 'UInt32Array'),
    ('float32', 'FloatArray'),
]))


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
