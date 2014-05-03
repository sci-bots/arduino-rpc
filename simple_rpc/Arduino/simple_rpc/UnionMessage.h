#ifndef ___UNION_MESSAGE__H___
#define ___UNION_MESSAGE__H___

#include "pb_encode.h"
#include "pb_decode.h"


/* This function reads manually the first tag from the stream and finds the
 * corresponding message type. It doesn't yet decode the actual message.
 *
 * Returns the tag number of the MsgType_fields array, allowing the caller to
 * identify the type of message. */
inline int decode_unionmessage_tag(pb_istream_t *stream,
                                   const pb_field_t union_fields_type[]) {
    pb_wire_type_t wire_type;
    uint32_t tag;
    bool eof;

    while (pb_decode_tag(stream, &wire_type, &tag, &eof)) {
        if (wire_type == PB_WT_STRING) {
            const pb_field_t *field;
            for (field = union_fields_type; field->tag != 0; field++) {
                if (field->tag == tag && (field->type & PB_LTYPE_SUBMESSAGE)) {
                    /* Found our field. */
                    return field->tag;
                }
            }
        }

        /* Wasn't our field.. */
        pb_skip_field(stream, wire_type);
    }
    return -1;
}


inline bool decode_unionmessage_contents(pb_istream_t *stream,
                                         const pb_field_t fields[],
                                         void *dest_struct) {
    pb_istream_t substream;
    bool status;
    if (!pb_make_string_substream(stream, &substream)) {
        return false;
    }

    status = pb_decode(&substream, fields, dest_struct);
    pb_close_string_substream(stream, &substream);
    return status;
}


/* This function is the core of the union encoding process. It handles
 * the top-level pb_field_t array manually, in order to encode a correct
 * field tag before the message. The pointer to MsgType_fields array is
 * used as an unique identifier for the message type.
 */
inline bool encode_unionmessage(pb_ostream_t *stream,
                                const pb_field_t union_fields_type[],
                                const pb_field_t messagetype[],
                                const void *message) {
    const pb_field_t *field;
    for (field = union_fields_type; field->tag != 0; field++) {
        if (field->ptr == messagetype) {
            /* This is our field, encode the message using it. */
            if (!pb_encode_tag_for_field(stream, field)) {
                return false;
            }

            return pb_encode_submessage(stream, messagetype, message);
        }
    }

    /* Didn't find the field for messagetype */
    return false;
}


#endif  // #ifndef ___UNION_MESSAGE__H___
