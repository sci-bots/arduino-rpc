/* This program reads a message from stdin, detects its type and decodes it.
 */

#include <iostream>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#include <pb_decode.h>
#include "UnionMessage.h"
#include "Array.h"
#include "commands.pb.h"


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


template <typename Int>
static bool read_int_array(pb_istream_t *stream, const pb_field_t *field,
                           void **arg) {
    Int &array = *((Int*)(*arg));
    uint64_t value;

    if (!pb_decode_varint(stream, &value)) {
      return false;
    }
    array.data[array.length] = value;
    array.length++;
    return true;
}


int main(int argc, char **argv) {
    /* Read the data into buffer */
    uint8_t buffer[512];
    if (argc != 2) {
      std::cerr << "usage: " << argv[0] << " <filename>" << std::endl;
      return -1;
    }

    FILE *input = fopen(argv[1], "r");
    size_t count = fread(buffer, 1, sizeof(buffer), input);
    pb_istream_t stream = pb_istream_from_buffer(buffer, count);

    int message_type = decode_unionmessage_tag(&stream, CommandRequest_fields);
    bool status = false;

    union {
      TotalRamSizeRequest total_ram_size;
      ArrayTestRequest array_test;
    } msg;

    void *msg_ptr = NULL;
    pb_field_t *fields_type;
    uint32_t array_buffer[10];
    union {
      UInt8Array uint8_t_;
      UInt16Array uint16_t_;
    } array;

    switch (message_type) {
      case CommandType_ARRAY_TEST:
        fields_type = (pb_field_t *)ArrayTestRequest_fields;
        array.uint8_t_.length = 0;
        array.uint8_t_.data = reinterpret_cast<uint8_t *>(&array_buffer[0]);
        msg.array_test.array.funcs.decode = &read_int_array<UInt8Array>;
        msg.array_test.array.arg = &array.uint8_t_;

        fields_type = (pb_field_t *)ArrayTestRequest_fields;
        printf("Got ArrayTestRequest: %d\n", message_type);
        break;
      case CommandType_TOTAL_RAM_SIZE:
        fields_type = (pb_field_t *)TotalRamSizeRequest_fields;
        printf("Got TotalRamSizeRequest: %d\n", message_type);
        break;
      default:
        printf("Unknown message type: %d\n", message_type);
        return 1;
    }

    status = decode_unionmessage_contents(&stream, fields_type, &msg);

    if (!status) {
        printf("Decode failed: %s\n", PB_GET_ERROR(&stream));
        return 1;
    } else {
      switch (message_type) {
        case CommandType_ARRAY_TEST:
          std::cout << "data: ";
          for (int i = 0; i < array.uint8_t_.length; i++) {
            std::cout << static_cast<int>(array.uint8_t_.data[i]);
            if (i < array.uint8_t_.length - 1) {
              std::cout << ", ";
            }
          }
          std::cout << std::endl;
          std::cout << "index: " << msg.array_test.index << std::endl;
          break;
        default:
          break;
      }
    }

    return 0;
}
