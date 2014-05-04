#ifndef ___NODE_COMMAND_PROCESSOR___
#define ___NODE_COMMAND_PROCESSOR___

#include "UnionMessage.h"
#include "commands.pb.h"


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
  buffer_with_len string_buffer_;
public:
  CommandProcessor(Obj &obj) : obj_(obj) {
    pinMode(13, OUTPUT);
  }

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
      TotalRamSizeRequest total_ram_size;

      RamDataSizeRequest ram_data_size;

      RamBssSizeRequest ram_bss_size;

      RamHeapSizeRequest ram_heap_size;

      RamStackSizeRequest ram_stack_size;

      RamFreeRequest ram_free;

      HighRequest high;

      LowRequest low;

      OutputRequest output;

      InputRequest input;

      PinModeRequest pin_mode;

      DigitalReadRequest digital_read;

      DigitalWriteRequest digital_write;

      AnalogReadRequest analog_read;

      AnalogWriteRequest analog_write;

      GetMillisRequest get_millis;

      GetMicrosRequest get_micros;

      ForwardI2cRequestRequest forward_i2c_request;
     } request;

    union {
      TotalRamSizeResponse total_ram_size;

      RamDataSizeResponse ram_data_size;

      RamBssSizeResponse ram_bss_size;

      RamHeapSizeResponse ram_heap_size;

      RamStackSizeResponse ram_stack_size;

      RamFreeResponse ram_free;

      HighResponse high;

      LowResponse low;

      OutputResponse output;

      InputResponse input;

      PinModeResponse pin_mode;

      DigitalReadResponse digital_read;

      DigitalWriteResponse digital_write;

      AnalogReadResponse analog_read;

      AnalogWriteResponse analog_write;

      GetMillisResponse get_millis;

      GetMicrosResponse get_micros;

      ForwardI2cRequestResponse forward_i2c_request;
     } response;

    pb_field_t *fields_type;
    bool status = true;

    pb_istream_t istream = pb_istream_from_buffer(buffer, request_size);

    int request_type = decode_unionmessage_tag(&istream,
                                               CommandRequest_fields);

    /* Set the sub-request fields type based on the decoded message identifier
     * tag, which corresponds to a value in the `CommandType` enumerated type.
     */
    switch (request_type) {
      case CommandType_TOTAL_RAM_SIZE:
        fields_type = (pb_field_t *)TotalRamSizeRequest_fields;
        break;
      case CommandType_RAM_DATA_SIZE:
        fields_type = (pb_field_t *)RamDataSizeRequest_fields;
        break;
      case CommandType_RAM_BSS_SIZE:
        fields_type = (pb_field_t *)RamBssSizeRequest_fields;
        break;
      case CommandType_RAM_HEAP_SIZE:
        fields_type = (pb_field_t *)RamHeapSizeRequest_fields;
        break;
      case CommandType_RAM_STACK_SIZE:
        fields_type = (pb_field_t *)RamStackSizeRequest_fields;
        break;
      case CommandType_RAM_FREE:
        fields_type = (pb_field_t *)RamFreeRequest_fields;
        break;
      case CommandType_HIGH:
        fields_type = (pb_field_t *)HighRequest_fields;
        break;
      case CommandType_LOW:
        fields_type = (pb_field_t *)LowRequest_fields;
        break;
      case CommandType_OUTPUT:
        fields_type = (pb_field_t *)OutputRequest_fields;
        break;
      case CommandType_INPUT:
        fields_type = (pb_field_t *)InputRequest_fields;
        break;
      case CommandType_PIN_MODE:
        fields_type = (pb_field_t *)PinModeRequest_fields;
        break;
      case CommandType_DIGITAL_READ:
        fields_type = (pb_field_t *)DigitalReadRequest_fields;
        break;
      case CommandType_DIGITAL_WRITE:
        fields_type = (pb_field_t *)DigitalWriteRequest_fields;
        break;
      case CommandType_ANALOG_READ:
        fields_type = (pb_field_t *)AnalogReadRequest_fields;
        break;
      case CommandType_ANALOG_WRITE:
        fields_type = (pb_field_t *)AnalogWriteRequest_fields;
        break;
      case CommandType_GET_MILLIS:
        fields_type = (pb_field_t *)GetMillisRequest_fields;
        break;
      case CommandType_GET_MICROS:
        fields_type = (pb_field_t *)GetMicrosRequest_fields;
        break;
      case CommandType_FORWARD_I2C_REQUEST:
        request.forward_i2c_request.request.funcs.decode = &read_string;
        request.forward_i2c_request.request.arg = &string_buffer_;
        fields_type = (pb_field_t *)ForwardI2cRequestRequest_fields;
        break;
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
      case CommandType_TOTAL_RAM_SIZE:
        fields_type = (pb_field_t *)TotalRamSizeResponse_fields;
        response.total_ram_size.result =
        obj_.total_ram_size();
        break;
      case CommandType_RAM_DATA_SIZE:
        fields_type = (pb_field_t *)RamDataSizeResponse_fields;
        response.ram_data_size.result =
        obj_.ram_data_size();
        break;
      case CommandType_RAM_BSS_SIZE:
        fields_type = (pb_field_t *)RamBssSizeResponse_fields;
        response.ram_bss_size.result =
        obj_.ram_bss_size();
        break;
      case CommandType_RAM_HEAP_SIZE:
        fields_type = (pb_field_t *)RamHeapSizeResponse_fields;
        response.ram_heap_size.result =
        obj_.ram_heap_size();
        break;
      case CommandType_RAM_STACK_SIZE:
        fields_type = (pb_field_t *)RamStackSizeResponse_fields;
        response.ram_stack_size.result =
        obj_.ram_stack_size();
        break;
      case CommandType_RAM_FREE:
        fields_type = (pb_field_t *)RamFreeResponse_fields;
        response.ram_free.result =
        obj_.ram_free();
        break;
      case CommandType_HIGH:
        fields_type = (pb_field_t *)HighResponse_fields;
        response.high.result =
        obj_.high();
        break;
      case CommandType_LOW:
        fields_type = (pb_field_t *)LowResponse_fields;
        response.low.result =
        obj_.low();
        break;
      case CommandType_OUTPUT:
        fields_type = (pb_field_t *)OutputResponse_fields;
        response.output.result =
        obj_.output();
        break;
      case CommandType_INPUT:
        fields_type = (pb_field_t *)InputResponse_fields;
        response.input.result =
        obj_.input();
        break;
      case CommandType_PIN_MODE:
        fields_type = (pb_field_t *)PinModeResponse_fields;

        obj_.pin_mode(request.pin_mode.pin, request.pin_mode.mode);
        break;
      case CommandType_DIGITAL_READ:
        fields_type = (pb_field_t *)DigitalReadResponse_fields;
        response.digital_read.result =
        obj_.digital_read(request.digital_read.pin);
        break;
      case CommandType_DIGITAL_WRITE:
        fields_type = (pb_field_t *)DigitalWriteResponse_fields;

        obj_.digital_write(request.digital_write.pin, request.digital_write.value);
        break;
      case CommandType_ANALOG_READ:
        fields_type = (pb_field_t *)AnalogReadResponse_fields;
        response.analog_read.result =
        obj_.analog_read(request.analog_read.pin);
        break;
      case CommandType_ANALOG_WRITE:
        fields_type = (pb_field_t *)AnalogWriteResponse_fields;

        obj_.analog_write(request.analog_write.pin, request.analog_write.value);
        break;
      case CommandType_GET_MILLIS:
        fields_type = (pb_field_t *)GetMillisResponse_fields;
        response.get_millis.result =
        obj_.get_millis();
        break;
      case CommandType_GET_MICROS:
        fields_type = (pb_field_t *)GetMicrosResponse_fields;
        response.get_micros.result =
        obj_.get_micros();
        break;
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
        if (Wire.endTransmission() == 0) {
          /* Transmission failed.  Perhaps slave was not ready or not
           * connected. */
          response.forward_i2c_request.result = 0;
          break;
        }

        /* Request response size. */
        buffer_size = Wire.requestFrom((uint8_t)request
                                       .forward_i2c_request.address,
                                       (uint8_t)1);
        if (buffer_size != 1) {
          /* Unexpected number of bytes. */
          response.forward_i2c_request.result = 0;
          break;
        }

        request_size = Wire.read();

        /* Request actual response. */
        buffer_size = Wire.requestFrom((uint8_t)request
                                       .forward_i2c_request.address,
                                       (uint8_t)request_size);
        if (buffer_size != request_size) {
          /* Unexpected response size. */
          response.forward_i2c_request.result = 0;
          break;
        }
        // Slave may send less than requested
        for (int i = 0; i < buffer_size; i++) {
          // receive a byte as character
          buffer[i] = Wire.read();
        }
        /* Return directly from here, since the I2C response is already
         * encoded and we wrote the encoded response directly to the
         * buffer. */
        return request_size;
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

#endif  // #ifndef ___NODE_COMMAND_PROCESSOR___
