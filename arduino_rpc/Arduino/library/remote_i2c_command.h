#ifndef ___REMOTE_I2C_COMMAND__H___
#define ___REMOTE_I2C_COMMAND__H___


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
  Wire.beginTransmission(i2c_address);
  Wire.write(buffer, ostream.bytes_written);
  return_code = Wire.endTransmission();
  if (return_code != 0) {
    /* Transmission failed.  Perhaps slave was not ready or not
     * connected. */
    return return_code;
  }

  status = false;
  /* Request response size. */
  for (int i = 0; i < 21; i++) {
    buffer_size = Wire.requestFrom(i2c_address, (uint8_t)1);
    if (buffer_size != 1) {
      /* Unexpected number of bytes. */
      return_code = -2;
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
      return_code = i2c_count;
      status = false;
      break;
    } else {
      /* The `i2c_count` should be valid. */
      response_size = i2c_count;
      return_code = i2c_count;
      status = true;
      break;
    }
  }
  if (!status) {
    /* An error was encountered so break. */
    return return_code;
  }

  /* Request actual response. */
  buffer_size = Wire.requestFrom(i2c_address, (uint8_t)response_size);
  if (buffer_size != response_size) {
    /* Unexpected response size. */
    return -100;
  }
  // Slave may send less than requested
  for (int i = 0; i < response_size; i++) {
    // receive a byte as character
    buffer[i] = Wire.read();
  }

  pb_istream_t istream = pb_istream_from_buffer(buffer, buffer_size);
  //memset(&response, 0, sizeof(response));

  decode_unionmessage_contents(&istream, response_fields, &response);
  return buffer_size;
}


int i2c_query(uint8_t address, uint8_t *msg, uint8_t *response,
              uint8_t byte_count) {
  Wire.beginTransmission(address);
  Wire.write(msg, byte_count);

  int result = Wire.endTransmission();
  if (result != 0) {
    /* Transmission failed.  Perhaps slave was not ready or not connected. */
    return result;
  }

  bool status = false;
  uint8_t i2c_count = 0;

  /* Request response size. */
  for (int i = 0; i < 21; i++) {
    byte_count = Wire.requestFrom(address, (uint8_t)1);
    if (byte_count != 1) {
      /* Unexpected number of bytes. */
      result = -2;
      status = false;
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
      break;
    } else {
      /* The `i2c_count` should be valid. */
      status = true;
      break;
    }
  }
  if (!status) {
    /* An error was encountered so break. */
    return -1;
  }

  /* Request actual response. */
  byte_count = Wire.requestFrom(address, i2c_count);
  if (byte_count != i2c_count) {
    /* Unexpected response size. */
    return -2;
  }
  // Slave may send less than requested
  for (int i = 0; i < i2c_count; i++) {
    // receive a byte as character
    response[i] = Wire.read();
  }
  /* Return directly from here, since the I2C response is already encoded and
    * we wrote the encoded response directly to the buffer. */
  return byte_count;
}


#endif
