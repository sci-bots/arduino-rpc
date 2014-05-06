'''
Templates for code generation.
'''


COMMAND_PROCESSOR_TEMPLATE = r'''
#ifndef ___COMMAND_PROCESSOR___
#define ___COMMAND_PROCESSOR___

#include "UnionMessage.h"
#include "{{ pb_header }}"


struct buffer_with_len {
  uint8_t buffer[16];
  uint8_t length;
};

{%- if disable_i2c %}
#ifndef DISABLE_I2C
#define DISABLE_I2C
#endif
{%- endif %}

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


template <typename Obj>
class CommandProcessor {
  /* # `CommandProcessor` #
   *
   * Each call to this functor processes a single command.
   *
   * All arguments are passed by reference, such that they may be used to form
   * a response.  If the integer return value of the call is zero, the call is
   * assumed to have no response required.  Otherwise, the arguments contain
   * must contain response values. */
protected:
  Obj &obj_;
#ifndef DISABLE_I2C
  buffer_with_len string_buffer_;
#endif  // #ifndef DISABLE_I2C
public:
  CommandProcessor(Obj &obj) : obj_(obj) {}

  int process_command(uint16_t request_size, uint16_t buffer_size,
                      uint8_t *buffer) {
    /* ## Call operator ##
     *
     * Arguments:
     *
     *  - `request`: Protocol buffer command request structure,
     *  - `buffer_size`: The number of bytes in the arguments buffer.
     *  - `data`: The arguments buffer. */

    union {
#ifndef DISABLE_I2C
      ForwardI2cRequestRequest forward_i2c_request;
#endif  // #ifndef DISABLE_I2C
    {%- for camel_name, underscore_name, return_type, args in commands %}
      {{ camel_name }}Request {{ underscore_name }};
    {%- endfor %}
    } request;

    union {
#ifndef DISABLE_I2C
      ForwardI2cRequestResponse forward_i2c_request;
#endif  // #ifndef DISABLE_I2C
    {%- for camel_name, underscore_name, return_type, args in commands %}
      {{ camel_name }}Response {{ underscore_name }};
    {%- endfor %}
    } response;

    pb_field_t *fields_type;
    bool status = true;
#ifndef DISABLE_I2C
    uint8_t i2c_count = 0;
#endif  // #ifndef DISABLE_I2C

    pb_istream_t istream = pb_istream_from_buffer(buffer, request_size);

    int request_type = decode_unionmessage_tag(&istream,
                                               CommandRequest_fields);

    /* Set the sub-request fields type based on the decoded message identifier
     * tag, which corresponds to a value in the `CommandType` enumerated type.
     */
    switch (request_type) {
#ifndef DISABLE_I2C
      case CommandType_FORWARD_I2C_REQUEST:
        request.forward_i2c_request.request.funcs.decode = &read_string;
        request.forward_i2c_request.request.arg = &string_buffer_;
        fields_type = (pb_field_t *)ForwardI2cRequestRequest_fields;
        break;
#endif  // #ifndef DISABLE_I2C
    {%- for camel_name, underscore_name, return_type, args in commands %}
      case CommandType_{{ underscore_name|upper }}:
        fields_type = (pb_field_t *){{ camel_name }}Request_fields;
        break;
    {%- endfor %}
      default:
        status = false;
        break;
    }

    if (!status) { return -1; }

    /* Deserialize request according to the fields type determined above. */
    decode_unionmessage_contents(&istream, fields_type, &request);

    pb_ostream_t ostream = pb_ostream_from_buffer(buffer, buffer_size);

    /* Process the request, and populate response fields as necessary. */
    switch (request_type) {
#ifndef DISABLE_I2C
      case CommandType_FORWARD_I2C_REQUEST:
        fields_type = (pb_field_t *)ForwardI2cRequestResponse_fields;
        /* Forward all bytes received on the local serial-stream to the i2c
         * bus. */
        /* Use the I2C master/slave data flow described [here][1].
         *
         *  1. Write request _(as master)_ to _slave_ device.
         *  2. Request a two-part response from the _slave_ device:
         *   a. Response length, in bytes, as an unsigned, 8-bit integer.
         *   b. Response of the length from 2(a).
         *
         * # Notes #
         *
         *  - Maximum of 32 bytes can be sent by the standard Wire library.
         *
         * ## Request data from slave ##
         *
         *  - The `Wire.requestFrom` function does not return until either the
         *    requested data is fully available, or an error occurred.
         *  - Building in a wait for `Wire.available` simply makes it possible
         *    for the code to hang forever if the data is not available.
         *
         * ## Send data from slave to master upon request ##
         *
         *  - You can only do one Wire.write in a `requestEvent` callback.
         *  - You do not do a `Wire.beginTransmission` or a
         *    `Wire.endTransmission`.
         *  - There is a limit of 32 bytes that can be returned.
         *
         * [1]: http://gammon.com.au/i2c-summary */
        Wire.beginTransmission((uint8_t)request.forward_i2c_request.address);
        Wire.write(string_buffer_.buffer, string_buffer_.length);
        response.forward_i2c_request.result = Wire.endTransmission();
        if (response.forward_i2c_request.result != 0) {
          /* Transmission failed.  Perhaps slave was not ready or not
           * connected. */
          response.forward_i2c_request.result = -1;
          break;
        }

        status = false;
        /* Request response size. */
        for (int i = 0; i < 21; i++) {
          buffer_size = Wire.requestFrom((uint8_t)request
                                         .forward_i2c_request.address,
                                         (uint8_t)1);
          if (buffer_size != 1) {
            /* Unexpected number of bytes. */
            response.forward_i2c_request.result = -2;
            status = false;
            break;
          }

          i2c_count = Wire.read();

          if (i2c_count == 0xFF) {
            /* The target is reporting that the request has not yet been
             * processed.  Try again... */
            if (i < 5) {
              /* Delay 1ms for the first 3 attempts, to allow fast requests to
               * return quickly. */
              delay(1);
            } else if (i < 10) {
              /* Delay 10ms for the first next 7 attempts. */
              delay(10);
            } else {
              /* For the last 20 attempts, double the delay each attempt, until
               * we reach 10240ms _(roughly 10 seconds)_. */
              delay(10 << (i - 10));
            }
          } else if (i2c_count > 32) {
            /* The buffer size is invalid. */
            response.forward_i2c_request.result = i2c_count;
            status = false;
            break;
          } else {
            /* The `i2c_count` should be valid. */
            request_size = i2c_count;
            response.forward_i2c_request.result = i2c_count;
            status = true;
            break;
          }
        }
        if (!status) {
          /* An error was encountered so break. */
          break;
        }

        /* Request actual response. */
        buffer_size = Wire.requestFrom((uint8_t)request
                                       .forward_i2c_request.address,
                                       (uint8_t)request_size);
        if (buffer_size != request_size) {
          /* Unexpected response size. */
          response.forward_i2c_request.result = request_size;
          break;
        }
        // Slave may send less than requested
        for (int i = 0; i < request_size; i++) {
          // receive a byte as character
          buffer[i] = Wire.read();
        }
        /* Return directly from here, since the I2C response is already
         * encoded and we wrote the encoded response directly to the
         * buffer. */
        return request_size;
#endif  // #ifndef DISABLE_I2C
    {%- for camel_name, underscore_name, return_type, args in commands %}
      case CommandType_{{ underscore_name|upper }}:
        fields_type = (pb_field_t *){{ camel_name }}Response_fields;
        {% if return_type %}response.{{ underscore_name }}.result ={% endif %}
        obj_.{{ underscore_name }}({% for arg in args %}request.{{ underscore_name }}.{{ arg.0 }}{% if not loop.last %}, {% endif %}{% endfor %});
        break;
    {%- endfor -%}
      default:
        return -1;
        break;
    }

    /* Serialize the response and write the encoded response to the buffer. */
    status = encode_unionmessage(&ostream, CommandResponse_fields, fields_type,
                                 &response);

    if (status) {
      return ostream.bytes_written;
    } else {
      return -1;
    }
  }
};

#endif  // #ifndef ___COMMAND_PROCESSOR___
'''


COMMAND_PROTO_DEFINITIONS = r'''
enum CommandType {
    FORWARD_I2C_REQUEST = 1;
{%- for underscore_name, key in command_names %}
    {{ underscore_name|upper }} = {{ key }};
{%- endfor %}
}

message ForwardI2cRequestRequest {
  required uint32 address = 1;
  required bytes request = 2;
}

{%- for camel_name, underscore_name, return_type, args in commands -%}
message {{ camel_name }}Request {
{%- for arg in args %}
    required {{ arg.1 }} {{ arg.0 }} = {{ loop.index }};
{%- endfor %}
}
{%- endfor %}

message ForwardI2cRequestResponse { required sint32 result = 1; }

{%- for camel_name, underscore_name, return_type, args in commands -%}
message {{ camel_name }}Response {
{%- if return_type %}
    required {{ return_type }} result = 1;
{% endif -%}
}
{%- endfor %}

message CommandRequest {
    optional ForwardI2cRequestRequest forward_i2c_request = 1;
{%- for camel_name, underscore_name, key in command_types %}
    optional {{ camel_name }}Request {{ underscore_name }} = {{ key }};
{%- endfor %}
}

message CommandResponse {
    optional ForwardI2cRequestResponse forward_i2c_request = 1;
{%- for camel_name, underscore_name, key in command_types %}
    optional {{ camel_name }}Response {{ underscore_name }} = {{ key }};
{%- endfor %}
}'''
