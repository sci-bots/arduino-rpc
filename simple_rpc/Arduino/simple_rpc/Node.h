#ifndef ___NODE__H___
#define ___NODE__H___

#include <stdint.h>

#ifdef ARDUINO
#include "Memory.h"
#else
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
  uint32_t total_ram_size() { return ram_size(); }
  uint32_t ram_data_size() { return data_size(); }
  uint32_t ram_bss_size() { return bss_size(); }
  uint32_t ram_heap_size() { return heap_size(); }
  uint32_t ram_stack_size() { return stack_size(); }
  uint32_t ram_free() { return free_memory(); }

  char test_char(char x) { return x; }
  uint8_t test_uint8(uint8_t x) { return x; }
  uint16_t test_uint16(uint16_t x) { return x; }
  int8_t test_int8(int8_t x) { return x; }
  int16_t test_int16(int16_t x) { return x; }
  int64_t test_int64(int64_t x) { return x; }
  float test_float(float x) { return x; }

  void set_led_state(int32_t state) { digitalWrite(led_pin_, state); }
  bool led_state() { return digitalRead(led_pin_); }

  uint8_t high() const { return HIGH; }
  uint8_t low() const { return LOW; }
  uint8_t output() const { return OUTPUT; }
  uint8_t input() const { return INPUT; }

  void pin_mode(uint8_t pin, uint8_t mode) { return pinMode(pin, mode); }
  bool digital_read(uint8_t pin) const { return digitalRead(pin); }
  void digital_write(uint8_t pin, uint8_t value) { digitalWrite(pin, value); }
  uint16_t analog_read(uint8_t pin) const { return analogRead(pin); }
  void analog_write(uint8_t pin, uint8_t value) { return analogWrite(pin, value); }
  uint32_t get_millis() const { return millis(); }
  uint32_t get_micros() const { return micros(); }
};


#endif  // #ifndef ___NODE__H___
