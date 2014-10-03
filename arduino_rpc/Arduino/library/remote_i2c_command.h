#ifndef ___REMOTE_I2C_COMMAND__H___
#define ___REMOTE_I2C_COMMAND__H___

#include <Array.h>


struct i2c_query {
  static const int8_t CREATED              =  10;
  static const int8_t QUERY_STARTED        =  20;
  static const int8_t SEND_FAILED          = -10;
  static const int8_t QUERY_LENGTH_FAILED  = -20;
  static const int8_t QUERY_ERROR          = -30;
  static const int8_t INVALID_BUFFER_SIZE  = -40;
  static const int8_t RESPONSE_SIZE_ERROR  = -50;
  static const int8_t RESPONSE_EMPTY_ERROR = -60;
  static const int8_t QUERY_COMPLETE       =  30;
  int8_t ERROR_CODE_;
  UInt8Array response_;

  UInt8Array cached_message_;
  uint8_t cached_address_;

  i2c_query() : ERROR_CODE_(CREATED), cached_address_(0) {}

  i2c_query(UInt8Array response)
      : ERROR_CODE_(CREATED), response_(response), cached_address_(0) {
    cached_message_ = {0, NULL};
  }

  uint16_t size() const { return response_.length; }

  UInt8Array repeat() {
    if (cached_address_ == 0) {
      return cached_message_;
    } else {
      return (*this)(cached_address_, cached_message_);
    }
  }

  UInt8Array operator() (uint8_t address, UInt8Array msg) {
    UInt8Array response = response_;

    ERROR_CODE_ = QUERY_STARTED;
    Wire.beginTransmission(address);
    Wire.write(msg.data, (uint8_t)msg.length);

    if (Wire.endTransmission() != 0) {
      /* Transmission failed.  Perhaps slave was not ready or not connected. */
      ERROR_CODE_ = SEND_FAILED;
      response = {0, NULL};
      return response;
    }

    bool status = false;
    uint8_t i2c_count = 0;

    /* Request response size. */
    for (int i = 0; i < 21; i++) {
      response.length = Wire.requestFrom(address, (uint8_t)1);
      if (response.length != 1) {
        /* Unexpected number of bytes. */
        status = false;
        ERROR_CODE_ = QUERY_LENGTH_FAILED;
        break;
      }

      i2c_count = Wire.read();

      if (i2c_count == 0xFF) {
        /* The target is reporting that the request has not yet been processed.
          * Try again... */
        if (i < 5) {
          /* Delay 1ms for the first 3 attempts, to allow fast requests to
            * return quickly. */
          delay(1);
        } else if (i < 10) {
          /* Delay 10ms for the first next 7 attempts. */
          delay(10);
        } else {
          /* For the last 20 attempts, double the delay each attempt, until we
            * reach 10240ms _(roughly 10 seconds)_. */
          delay(10 << (i - 10));
        }
      } else if (i2c_count > 32) {
        /* The buffer size is invalid. */
        status = false;
        ERROR_CODE_ = INVALID_BUFFER_SIZE;
        break;
      } else {
        /* The `i2c_count` should be valid. */
        status = true;
        break;
      }
    }
    if (!status) {
      /* An error was encountered so break. */
      ERROR_CODE_ = QUERY_ERROR;
      response = {0, NULL};
      return response;
    }

    /* Request actual response. */
    response.length = Wire.requestFrom(address, (uint8_t)i2c_count);
    if (response.length != i2c_count || i2c_count > response_.length) {
      /* Unexpected response size. */
      ERROR_CODE_ = RESPONSE_SIZE_ERROR;
      response = {0, NULL};
      return response;
    }

    // Slave may send less than requested
    for (int i = 0; i < i2c_count; i++) {
      // receive a byte as character
      response_.data[i] = Wire.read();
    }

    /* Return directly from here, since the I2C response is already encoded and
     * we wrote the encoded response directly to the buffer. */
    if (response.length == 0) {
      ERROR_CODE_ = RESPONSE_EMPTY_ERROR;
    } else {
      ERROR_CODE_ = QUERY_COMPLETE;
      cached_message_ = msg;
      cached_address_ = address;
    }
    return response;
  }
};


template<typename Request, typename Response>
int8_t remote_i2c_command(uint8_t i2c_address,
                          Request &request, Response &response,
                          const pb_field_t *command_request_fields,
                          const pb_field_t *request_fields,
                          const pb_field_t *response_fields,
                          uint8_t *buffer, uint8_t buffer_size) {
  uint8_t i2c_count = 0;
  uint16_t response_size = 0;
  int8_t return_code = -30;

  pb_ostream_t ostream = pb_ostream_from_buffer(buffer, buffer_size);

  /* Serialize the response and write the encoded response to the buffer. */
  bool status = encode_unionmessage(&ostream, command_request_fields,
                                    request_fields, &request);


  return_code = i2c_query(i2c_address, buffer, buffer, ostream.bytes_written);
  if (return_code < 0) {
    return return_code;
  }

  pb_istream_t istream = pb_istream_from_buffer(buffer, return_code);

  decode_unionmessage_contents(&istream, response_fields, &response);
  return buffer_size;
}

#endif
