#ifndef ___ARRAY_SERIALIZATION__H___
#define ___ARRAY_SERIALIZATION__H___

#include "Array.h"


static bool read_string(pb_istream_t *stream, const pb_field_t *field,
                        void **arg) {
    UInt8Array &buffer = *((UInt8Array*)(*arg));
    size_t len = stream->bytes_left;

    if (len > buffer.length - 1 || !pb_read(stream, &buffer.data[0], len)) {
      buffer.length = 0;
      return false;
    }

    buffer.length = len;
    return true;
}


static bool read_byte_array(pb_istream_t *stream, const pb_field_t *field,
                            void **arg) {
    UInt8Array &array = *((UInt8Array*)(*arg));
    size_t len = stream->bytes_left;

    if (len > array.length || !pb_read(stream, &array.data[0], len)) {
      array.length = 0;
      return false;
    }

    array.length = len;
    return true;
}


static bool write_byte_array(pb_ostream_t *stream, const pb_field_t *field,
                             void * const *arg) {
    UInt8Array const &array = *((UInt8Array const *)(*arg));

    if (!pb_encode_tag(stream, PB_WT_STRING, field->tag)) {
      return false;
    }
    pb_encode_varint(stream, array.length);
    return pb_write(stream, &array.data[0], array.length);
}


static bool write_float_array(pb_ostream_t *stream, const pb_field_t *field,
                              void * const *arg) {
    UInt8Array const &array = *((UInt8Array const *)(*arg));
    float value;

    if (!pb_encode_tag(stream, PB_WT_STRING, field->tag)) {
      return false;
    }
    pb_ostream_t substream = PB_OSTREAM_SIZING;

    for (int i = 0; i < array.length; i++) {
      pb_encode_fixed32(&substream, &array.data[i]);
    }

    pb_encode_varint(stream, substream.bytes_written);

    for (int i = 0; i < array.length; i++) {
      pb_encode_fixed32(stream, &array.data[i]);
    }
    return true;
}


template <typename Float>
static bool read_float_array(pb_istream_t *stream, const pb_field_t *field,
                             void **arg) {
    Float &array = *((Float*)(*arg));
    float value;

    if (!pb_decode_fixed32(stream, &value)) {
      return false;
    }
    array.data[array.length] = value;
    array.length++;
    return true;
}


template <typename Float>
static bool write_float_array(pb_ostream_t *stream, const pb_field_t *field,
                            void * const *arg) {
    Float const &array = *((Float const *)(*arg));
    float value;

    if (!pb_encode_tag(stream, PB_WT_STRING, field->tag)) {
      return false;
    }
    pb_ostream_t substream = PB_OSTREAM_SIZING;

    for (int i = 0; i < array.length; i++) {
      pb_encode_fixed32(&substream, &array.data[i]);
    }

    pb_encode_varint(stream, substream.bytes_written);

    for (int i = 0; i < array.length; i++) {
      pb_encode_fixed32(stream, &array.data[i]);
    }
    return true;
}


template <typename ArrayType>
static bool read_uint_array(pb_istream_t *stream, const pb_field_t *field,
                           void **arg) {
    ArrayType &array = *((ArrayType*)(*arg));
    uint64_t value;

    if (!pb_decode_varint(stream, &value)) {
      return false;
    }
    array.data[array.length] = value;
    array.length++;
    return true;
}


template <typename Int>
static bool read_int_array(pb_istream_t *stream, const pb_field_t *field,
                           void **arg) {
    Int &array = *((Int*)(*arg));
    int64_t value;

    if (!pb_decode_svarint(stream, &value)) {
      return false;
    }
    array.data[array.length] = value;
    array.length++;
    return true;
}


template <typename Int, typename T>
static bool write_uint_array(pb_ostream_t *stream, const pb_field_t *field,
                             void * const *arg) {
    Int const &array = *((Int const *)(*arg));

    if (!pb_encode_tag(stream, PB_WT_STRING, field->tag)) {
      return false;
    }
    pb_ostream_t substream = PB_OSTREAM_SIZING;

    for (int i = 0; i < array.length; i++) {
      pb_encode_varint(&substream, array.data[i]);
    }

    pb_encode_varint(stream, substream.bytes_written);

    for (int i = 0; i < array.length; i++) {
      pb_encode_varint(stream, array.data[i]);
    }
    return true;
}


template <typename Int, typename T>
static bool write_int_array(pb_ostream_t *stream, const pb_field_t *field,
                            void * const *arg) {
    Int const &array = *((Int const *)(*arg));
    int64_t value;

    if (!pb_encode_tag(stream, PB_WT_STRING, field->tag)) {
      return false;
    }
    pb_ostream_t substream = PB_OSTREAM_SIZING;

    for (int i = 0; i < array.length; i++) {
      pb_encode_svarint(&substream, array.data[i]);
    }

    pb_encode_varint(stream, substream.bytes_written);

    for (int i = 0; i < array.length; i++) {
      pb_encode_svarint(stream, array.data[i]);
    }
    return true;
}

#endif  // #ifndef ___ARRAY_SERIALIZATION__H___
