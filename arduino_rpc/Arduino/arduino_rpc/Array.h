#ifndef ___ARRAY__H___
#define ___ARRAY__H___

#include <stdint.h>


class UInt8Array {
public:
  uint8_t length;
  uint8_t *data;
};


class UInt16Array {
public:
  uint8_t length;
  uint16_t *data;
};

#endif  // #ifndef ___ARRAY__H___
