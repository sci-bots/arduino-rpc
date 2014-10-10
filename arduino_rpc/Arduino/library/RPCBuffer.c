#include "RPCBuffer.h"


/* To save RAM, the serial-port interface may be disabled by defining
 * `DISABLE_SERIAL`. */
#ifndef DISABLE_SERIAL
uint8_t packet_buffer[PACKET_SIZE];
#endif  // #ifndef DISABLE_SERIAL

/*  - Allocate buffer for command-processor to extract/write array data. */
uint8_t command_array_buffer[COMMAND_ARRAY_BUFFER_SIZE];
uint8_t i2c_packet_buffer[I2C_PACKET_SIZE];
