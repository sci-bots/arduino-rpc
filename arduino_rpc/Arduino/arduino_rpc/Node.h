#ifndef ___NODE__H___
#define ___NODE__H___

#include <stdint.h>
#include <EEPROM.h>
#include "Memory.h"
#include "Array.h"
#define BROADCAST_ADDRESS 0x00


/* Callback functions for slave device. */
extern void i2c_receive_event(int byte_count);
extern void i2c_request_event();


class Node {
public:
  static const uint16_t EEPROM__I2C_ADDRESS = 0x00;
  uint8_t i2c_address_;

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
  uint8_t array_demo(UInt8Array array, uint8_t index) {
    if (index < array.length) {
      /* Return value from array at the specified index.
       *
       * This isn't particularly useful, but it makes it possible to verify
       * that the array is received intact. */
      return array.data[index];
    } else {
      /* Index is out-of-range. */
      return 0xFF;
    }
  }
};


#endif  // #ifndef ___NODE__H___
