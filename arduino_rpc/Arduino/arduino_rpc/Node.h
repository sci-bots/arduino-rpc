#ifndef ___NODE__H___
#define ___NODE__H___

#include <stdint.h>
#include <EEPROM.h>
#include "Memory.h"
#include "Array.h"
#include "custom_pb.h"
#define BROADCAST_ADDRESS 0x00


/* Callback functions for slave device. */
extern void i2c_receive_event(int byte_count);
extern void i2c_request_event();


class Node {
public:
  static const uint16_t EEPROM__I2C_ADDRESS = 0x00;
  uint8_t i2c_address_;
  uint8_t output_buffer[10];

  Node() {
    i2c_address_ = EEPROM.read(EEPROM__I2C_ADDRESS);
    Wire.begin(i2c_address_);
  }
  uint32_t ram_free() { return free_memory(); }

  void pin_mode(uint8_t pin, uint8_t mode) { return pinMode(pin, mode); }
  void delay_ms(uint32_t milliseconds) const { delay(milliseconds); }
  bool digital_read(uint8_t pin) const { return digitalRead(pin); }
  void digital_write(uint8_t pin, uint8_t value) { digitalWrite(pin, value); }
  uint16_t analog_read(uint8_t pin) const { return analogRead(pin); }
  void analog_write(uint8_t pin, uint8_t value) { return analogWrite(pin, value); }
  int i2c_address() const { return i2c_address_; }
  int set_i2c_address(uint8_t address) {
    i2c_address_ = address;
    Wire.begin(address);
    // Write the value to the appropriate byte of the EEPROM.
    // These values will remain there when the board is turned off.
    EEPROM.write(EEPROM__I2C_ADDRESS, i2c_address_);
    return address;
  }

  Int32Array ret_array_demo(Int32Array array) {
    if (array.length > 3) {
      array.data = array.data + array.length - 3;
      array.length = 3;
    }
    return array;
  }

  UInt16Array reverse_array_demo(UInt16Array array) {
    for(int i = 0; i < static_cast<int>(array.length / 2); i++) {
      uint16_t temp = array.data[i];
      array.data[i] = array.data[array.length - 1 - i];
      array.data[array.length - 1 - i] = temp;
    }
    return array;
  }

  UInt8Array str_demo() {
    /* # `str_demo` #
     *
     * This method demonstrates how to return a string of characters stored in
     * program memory as an array of bytes.
     *
     * ## Example Python code ##
     *
     *     >>> import numpy as np
     *     >>> from arduino_rpc.board import ArduinoRPCBoard
     *     >>> b = ArduinoRPCBoard('/dev/ttyUSB1')
     *
     *     free memory: 270
     *     >>> np.array(b.str_demo(), dtype=np.uint8).tostring()
     *     'hello'
     */
    UInt8Array result;
    result.data = reinterpret_cast<uint8_t *>(&output_buffer[0]);
    strcpy_P(reinterpret_cast<char *>(result.data), PSTR("hello"));
    result.length = 5;
    return result;
  }

  UInt8Array pin_state(uint8_t const pin_id) {
    /* # `pin_state` #
     *
     * This method demonstrates how to return an encoded custom Protocol
     * Buffers message type as a byte string.
     *
     * ## Example Python code ##
     *
     *
     *     >>> from arduino_rpc.protobuf_custom import PinState
     *     >>> from arduino_rpc.board import ArduinoRPCBoard
     *     >>> b = ArduinoRPCBoard('/dev/ttyUSB0')
     *
     *     free memory: 190
     *
     * First, we read the current state of pin 13.
     *
     *     >>> p = PinState.FromString(b.pin_state(pin_id=13))
     *     >>> dict([(k, getattr(p, k)) for k in ('pin_id', 'state')])
     *     {'pin_id': 13, 'state': False}
     *
     * Notice that pin 13 is off _(i.e., `False`)_.  Now, we turn pin 13 on by
     * writing a value of `1`, and read the pin state again.
     *
     *     >>> b.digital_write(pin=13, value=1)
     *     <arduino_rpc.protobuf_commands.DigitalWriteResponse object at 0x7fb364b37ec0>
     *     >>> p = PinState.FromString(b.pin_state(pin_id=13))
     *     >>> dict([(k, getattr(p, k)) for k in ('pin_id', 'state')])
     *     {'pin_id': 13, 'state': True}
     *
     * Notice that pin 13 is now on _(i.e., `True`)_.
     */

    /* ## Serialize Protocol Buffer message ## */
    /*  - Construct and populate `PinState` Protocol Buffer message. */
    PinState state;

    state.pin_id = pin_id;
    state.state = digitalRead(pin_id);

    /*  - Wrap `output_buffer` array as a `nanopb` output stream. */
    pb_ostream_t stream = pb_ostream_from_buffer(output_buffer,
                                                 sizeof(output_buffer));
    /*  - Serialize/encode `state` structure to output stream. */
    pb_encode(&stream, PinState_fields, &state);

    /* Construct `UInt8Array` return type, using the address of the output
     * buffer and the number of bytes written to the output stream. */
    UInt8Array result;
    result.data = &output_buffer[0];
    result.length = stream.bytes_written;
    return result;
  }
};


#endif  // #ifndef ___NODE__H___
