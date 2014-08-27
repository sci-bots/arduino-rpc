'''
Templates for code generation.
'''


COMMAND_PROCESSOR_TEMPLATE = r'''
#ifndef ___COMMAND_PROCESSOR___
#define ___COMMAND_PROCESSOR___

#include "UnionMessage.h"
#include "Array.h"
#include "ArraySerialization.h"
#include "{{ pb_header }}"


{%- if disable_i2c %}
#ifndef DISABLE_I2C
#define DISABLE_I2C
#endif
{%- endif %}


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
  static const size_t DEFAULT_ARRAY_BUFFER_SIZE = 48;
  UInt8Array array_buffer_;
  union {
    Int8Array int8_t_;
    Int16Array int16_t_;
    Int32Array int32_t_;
    UInt8Array uint8_t_;
    UInt16Array uint16_t_;
    UInt32Array uint32_t_;
    FloatArray float_;
  } array_;
  union {
    Int8Array int8_t_;
    Int16Array int16_t_;
    Int32Array int32_t_;
    UInt8Array uint8_t_;
    UInt16Array uint16_t_;
    UInt32Array uint32_t_;
    FloatArray float_;
  } return_array_;
public:
  CommandProcessor(Obj &obj) : obj_(obj) {
    /*  - No buffer was provided so allocate default buffer of 48 bytes. */
    array_buffer_.data = reinterpret_cast<uint8_t *>(
      malloc(DEFAULT_ARRAY_BUFFER_SIZE));
    array_buffer_.length = DEFAULT_ARRAY_BUFFER_SIZE;
  }

  CommandProcessor(Obj &obj, UInt8Array array_buffer)
    : obj_(obj), array_buffer_(array_buffer) {}

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
        array_.uint8_t_.length = array_buffer_.length;
        array_.uint8_t_.data = array_buffer_.data;
        request.forward_i2c_request.request.funcs.decode = &read_string;
        request.forward_i2c_request.request.arg = &array_.uint8_t_;
        fields_type = (pb_field_t *)ForwardI2cRequestRequest_fields;
        break;
#endif  // #ifndef DISABLE_I2C
    {%- for camel_name, underscore_name, return_type, args in commands %}
      case CommandType_{{ underscore_name|upper }}:
    {%- for name, type_info in args -%}
    {%- if type_info.1 == 'array' %}
        /* Array: {{ name }}, {{ type_info.0 }}, {{ type_info.1 }}, {{ type_info.2 }} */
        array_.{{ type_info.0 }}_.length = 0;
        array_.{{ type_info.0 }}_.data = reinterpret_cast<{{ type_info.0 }} *>(array_buffer_.data);
        request.{{ underscore_name }}.{{ name }}.funcs.decode = &read_
        {%- if type_info.0 == 'float' -%}float
        {%- else %}{%- if return_type.0 == 'uint8_t' -%}byte
        {%- else %}{%- if type_info.0.startswith('u') %}uint
        {%- else %}int
        {%- endif -%}{%- endif -%}{%- endif -%}
        _array{%- if return_type.0 != 'uint8_t' -%}<{{ type_info.2 }}>{%- endif %};
        request.{{ underscore_name }}.{{ name }}.arg = &array_.{{ type_info.0 }}_;
    {% endif -%}
    {%- endfor %}
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
        Wire.write(array_.uint8_t_.data, array_.uint8_t_.length);
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
        // `return_type`: {{ return_type }}
        {% if return_type -%}
        {%- if return_type.1 == 'array' %}
        response.{{ underscore_name }}.result.funcs.encode = &write_
        {%- if return_type.0 == 'float' -%}float
        {%- else %}{%- if return_type.0 == 'uint8_t' -%}byte
        {%- else %}{% if return_type.0.startswith('u') %}uint
        {%- else %}int
        {%- endif -%}{% endif -%}{%- endif -%}
        _array
        {%- if return_type.0 != 'uint8_t' -%}
        <{{ return_type.2 }}
        {%- if return_type.0 != 'float' -%}
        , {{ return_type.0 }}
        {%- endif -%}
        >{%- endif -%};
        response.{{ underscore_name }}.result.arg = &return_array_.{{ return_type.0 }}_;
        return_array_.{{ return_type.0 }}_ =
        {% else %}
        response.{{ underscore_name }}.result ={% endif %}{% endif %}
        obj_.{{ underscore_name }}(
        {%- for name, type_info in args -%}
        {%- if type_info.1 == 'array' %}
            array_.{{ type_info.0 }}_
        {% else %}
            request.{{ underscore_name }}.{{ name }}
        {% endif -%}
        {%- if not loop.last %}, {% endif %}
        {%- endfor %});
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
{%- if not disable_i2c %}
    FORWARD_I2C_REQUEST = 1;
{%- endif %}
{%- for underscore_name, key in command_names %}
    {{ underscore_name|upper }} = {{ key }};
{%- endfor %}
}

{%- if not disable_i2c %}
message ForwardI2cRequestRequest {
  required uint32 address = 1;
  required bytes request = 2;
}
{%- endif %}

{%- for camel_name, underscore_name, return_type, args in commands -%}
message {{ camel_name }}Request {
{%- for arg in args -%}
{%- if arg.1|length == 2 %}
    {{ arg.1.1 }} {{ arg.1.0 }} {{ arg.0 }} = {{ loop.index }}
    {%- if arg.1.0 != 'bytes' %} [packed=true] {% endif %};
{%- else %}
    required {{ arg.1 }} {{ arg.0 }} = {{ loop.index }};
{%- endif %}
{%- endfor %}
}
{%- endfor %}

{%- if not disable_i2c %}
message ForwardI2cRequestResponse { required sint32 result = 1; }
{%- endif %}

{%- for camel_name, underscore_name, return_type, args in commands -%}
message {{ camel_name }}Response {
{%- if return_type %}
{%- if return_type|length == 2 %}
    {{ return_type.1 }} {{ return_type.0 }} result = 1
    {%- if return_type.0 != 'bytes' %} [packed=true] {% endif %};
{%- else %}
    required {{ return_type }} result = 1;
{%- endif %}
{% endif -%}
}
{%- endfor %}

message CommandRequest {
{%- if not disable_i2c %}
    optional ForwardI2cRequestRequest forward_i2c_request = 1;
{%- endif %}
{%- for camel_name, underscore_name, key in command_types %}
    optional {{ camel_name }}Request {{ underscore_name }} = {{ key }};
{%- endfor %}
}

message CommandResponse {
{%- if not disable_i2c %}
    optional ForwardI2cRequestResponse forward_i2c_request = 1;
{%- endif %}
{%- for camel_name, underscore_name, key in command_types %}
    optional {{ camel_name }}Response {{ underscore_name }} = {{ key }};
{%- endfor %}
}'''
