#ifndef ___ARRAY_SERIALIZATION__H___
#define ___ARRAY_SERIALIZATION__H___


struct buffer_with_len {
  uint8_t buffer[16];
  uint8_t length;
};


static bool read_string(pb_istream_t *stream, const pb_field_t *field,
                        void **arg) {
    buffer_with_len &buffer = *((buffer_with_len*)(*arg));
    size_t len = stream->bytes_left;

    if (len > sizeof(buffer.buffer) - 1 ||
        !pb_read(stream, &buffer.buffer[0], len)) {
      buffer.length = 0;
      return false;
    }

    buffer.length = len;
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


template <typename Int>
static bool read_uint_array(pb_istream_t *stream, const pb_field_t *field,
                           void **arg) {
    Int &array = *((Int*)(*arg));
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
    uint64_t value;

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
