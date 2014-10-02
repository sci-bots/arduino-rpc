#ifndef ___I2C_HANDLER__H___
#define ___I2C_HANDLER__H___

#include <Wire.h>
#include <Packet.h>

struct I2CHandlerClass {
  static uint8_t *i2c_packet_buffer_;
  static uint8_t processing_i2c_request_;
  static uint8_t i2c_response_size_sent_;
  static FixedPacket i2c_packet_;

  static void begin(uint8_t *buffer, size_t buffer_size) {
    i2c_packet_buffer_ = buffer;
    i2c_packet_.reset_buffer(buffer_size, &i2c_packet_buffer_[0]);
    processing_i2c_request_ = false;
    i2c_response_size_sent_ = false;
  }

  static void i2c_receive_event(int byte_count) {
    processing_i2c_request_ = true;
    /* Record all bytes received on the i2c bus to a buffer.  The contents of
     * this buffer will be forwarded to the local serial-stream. */
    int i;
    for (i = 0; i < byte_count; i++) {
        i2c_packet_buffer_[i] = Wire.read();
    }
    i2c_packet_.payload_length_ = i;
    i2c_packet_.type(Packet::packet_type::DATA);
  }

  static void i2c_request_event() {
    uint8_t byte_count = (uint8_t)i2c_packet_.payload_length_;
    /* There is a response from a previously received packet, so send it to the
     * master of the i2c bus. */
    if (!i2c_response_size_sent_) {
      if (processing_i2c_request_) {
        Wire.write(0xFF);
      } else {
        Wire.write(byte_count);
        i2c_response_size_sent_ = true;
      }
    } else {
      Wire.write(i2c_packet_.payload_buffer_, byte_count);
      i2c_response_size_sent_ = false;
    }
  }

  template <typename Processor>
  static void parse_available(Processor &command_processor) {
    if (processing_i2c_request_) {
      process_packet_with_processor(i2c_packet_, command_processor);
      processing_i2c_request_ = false;
    }
  }
};


extern I2CHandlerClass I2CHandler;

#endif  // #ifndef ___I2C_HANDLER__H___
