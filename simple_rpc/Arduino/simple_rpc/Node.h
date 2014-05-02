#ifndef ___NODE__H___
#define ___NODE__H___

#include <stdint.h>

#ifndef ARDUINO
inline uint32_t ram_size() { return 0; }
inline uint32_t ram_size() { return 0; }
inline uint32_t data_size() { return 0; }
inline uint32_t bss_size() { return 0; }
inline uint32_t heap_size() { return 0; }
inline uint32_t stack_size() { return 0; }
inline uint32_t free_memory() { return 0; }
inline void pinMode(int pin, int value) {}
inline uint32_t digitalRead(int pin) { return 0; }
inline void digitalWrite(int pin, int value) {}
#endif  // #ifndef ARDUINO


class Node {
  uint8_t led_pin_;
public:
  Node(uint8_t led_pin) : led_pin_(led_pin) {
   pinMode(led_pin_, OUTPUT);
   set_led_state(false);
  }
  void begin() {}
  void echo() {}
  uint32_t ram_size() { return ram_size(); }
  uint32_t ram_data_size() { return data_size(); }
  uint32_t ram_bss_size() { return bss_size(); }
  uint32_t ram_heap_size() { return heap_size(); }
  uint32_t ram_stack_size() { return stack_size(); }
  uint32_t ram_free() { return free_memory(); }
  void set_led_state(int32_t state) { digitalWrite(led_pin_, state); }
  bool led_state() { return digitalRead(led_pin_); }
  char test_char(char x) { return x; }
  uint8_t test_uint8(uint8_t x) { return x; }
  uint16_t test_uint16(uint16_t x) { return x; }
  int8_t test_int8(int8_t x) { return x; }
  int16_t test_int16(int16_t x) { return x; }
  int64_t test_int64(int64_t x) { return x; }
  float test_float(float x) { return x; }
};


#endif  // #ifndef ___NODE__H___
