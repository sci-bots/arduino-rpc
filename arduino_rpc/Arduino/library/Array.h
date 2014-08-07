#ifndef ___ARRAY__H___
#define ___ARRAY__H___

#include <stdint.h>


class Int8Array {
public:
  uint16_t length;
  int8_t *data;
};


class Int16Array {
public:
  uint16_t length;
  int16_t *data;
};


class Int32Array {
public:
  uint16_t length;
  int32_t *data;
};


class UInt8Array {
public:
  uint16_t length;
  uint8_t *data;
};


class UInt16Array {
public:
  uint16_t length;
  uint16_t *data;
};


class UInt32Array {
public:
  uint16_t length;
  uint32_t *data;
};


class FloatArray {
public:
  uint16_t length;
  float *data;
};

#endif  // #ifndef ___ARRAY__H___
