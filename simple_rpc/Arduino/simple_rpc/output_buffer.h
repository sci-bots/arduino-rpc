#ifndef  ___OUTPUT_BUFFER__H___
#define  ___OUTPUT_BUFFER__H___

#include "Arduino.h"

extern char output_buffer[];

#define P(str) (strcpy_P(output_buffer, PSTR(str)), output_buffer)

#endif  // ___OUTPUT_BUFFER__H___
