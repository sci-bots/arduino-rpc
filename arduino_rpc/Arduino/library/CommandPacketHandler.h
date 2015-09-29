#ifndef ___COMMAND_PACKET_HANDLER__H___
#define ___COMMAND_PACKET_HANDLER__H___


#include "CArrayDefs.h"
#include "PacketWriter.h"


/* # `process_packet` # */
template <typename Packet, typename Processor>
UInt8Array process_packet_with_processor(Packet &packet,
                                         Processor &processor) {
    uint16_t payload_bytes_to_process = packet.payload_length_;

    UInt8Array result;
    if (packet.type() == Packet::packet_type::DATA &&
        payload_bytes_to_process > 0) {
#if defined (SERIAL_DEBUG) && defined (DISABLE_SERIAL)
      /* Dump packet payload bytes as hex characters. */
      for (int i = 0; i < packet.payload_length_; i++) {
          Serial.print(packet.payload_buffer_[i], HEX);
          if (i < packet.payload_length_ - 1) {
            Serial.print(", ");
          }
          Serial.println("");
      }
#endif
      UInt8Array request;
      UInt8Array buffer;
      request.data = packet.payload_buffer_;
      request.length = packet.payload_length_;
      buffer = request;
      buffer.length = packet.buffer_size_;
      result = processor.process_command(request, buffer);
    } else {
      result.data = NULL;
      result.length = 0xffff;  // data = NULL;
    }
    return result;
}


template <typename OStream, typename CommandProcessor>
class CommandPacketHandler {
  /* # `CommandPacketHandler` #
   *
   * This class extracts a command _(with a corresponding data buffer, if
   * applicable)_ from a `Packet`.  This is performed by having calling code
   * call the `process_packet` method, passing in the packet to be processed.
   *
   * __NB__ The packet state is intended to be updated by the `process_packet`
   * command to contain the response to send via the `OStream` interface.  For
   * example, a command may return a result value/structure to the source of
   * the request by writing data to the `packet.payload_buffer_`, provided the
   * data is no longer than `packet.buffer_size_`.
   *
   * If no response should be sent, the type of the packet must be set to
   * `Packet::packet_type::NONE`. */
  public:

  OStream &ostream_;
  CommandProcessor &command_processor_;

  CommandPacketHandler(OStream &ostream, CommandProcessor &command_processor)
    : ostream_(ostream), command_processor_(command_processor) {}

  template <typename Packet>
  void process_packet(Packet &packet) {
    UInt8Array result = process_packet_with_processor(packet,
                                                      command_processor_);
    FixedPacket result_packet;
    if (result.data == NULL && result.length > 0) {
      /* There was an error encountered while processing the request. */
      result_packet.type(FixedPacket::packet_type::NACK);
      result_packet.payload_length_ = 0;
    } else {
      result_packet.reset_buffer(result.length, result.data);
      result_packet.payload_length_ = result.length;
      result_packet.type(FixedPacket::packet_type::DATA);
    }
    write_packet(ostream_, result_packet);
  }
};


#endif  // #ifndef ___COMMAND_PACKET_HANDLER__H___
