#ifndef ___NODE__H___
#define ___NODE__H___

#include <stdint.h>
#include "Memory.h"
#include "Array.h"
#define BROADCAST_ADDRESS 0x00


/* Callback functions for slave device. */
extern void i2c_receive_event(int byte_count);
extern void i2c_request_event();


class Node {
public:
  uint32_t total_ram_size() { return ram_size(); }
  uint32_t ram_data_size() { return data_size(); }
  uint32_t ram_bss_size() { return bss_size(); }
  uint32_t ram_heap_size() { return heap_size(); }
  uint32_t ram_stack_size() { return stack_size(); }
  uint32_t ram_free() { return free_memory(); }

  void pin_mode(uint8_t pin, uint8_t mode) { return pinMode(pin, mode); }
  void delay_ms(uint32_t milliseconds) const { delay(milliseconds); }
  bool digital_read(uint8_t pin) const { return digitalRead(pin); }
  void digital_write(uint8_t pin, uint8_t value) { digitalWrite(pin, value); }
  uint16_t analog_read(uint8_t pin) const { return analogRead(pin); }
  void analog_write(uint8_t pin, uint8_t value) { return analogWrite(pin, value); }
  uint32_t get_millis() const { return millis(); }
  uint32_t get_micros() const { return micros(); }

  uint8_t array_test(UInt8Array array, uint8_t index) {
    /* TODO:
     *
     * There seems to be a bug in `nanopb`.
     *
     *     >>> data = range(5, 0, -1)
     *     >>> data
     *     [5, 4, 3, 2, 1]
     *     >>> [node.array_test(array=data, index=i) for i, d in enumerate(data)]
     *     [5, 4, 3, 2, 1]
     *     >>> data = range(5)
     *     >>> data
     *     [0, 1, 2, 3, 4]
     *     >>> [node.array_test(array=data, index=i) for i, d in enumerate(data)]
     *     [0, 0, 0, 0, 0]
     *
     * The last response should be `[0, 1, 2, 3, 4]`, not `[0, 0, 0, 0, 0]`
     */
    if (index < array.length) {
      return array.data[index];
    } else {
      return 0xFF;
    }
  }

  uint16_t uint16_array_test(UInt16Array array) {
    return array.length;
    //if (index < array.length) {
      //return array.data[index];
    //} else {
      //return 0xFFFF;
    //}
  }
};


#endif  // #ifndef ___NODE__H___
