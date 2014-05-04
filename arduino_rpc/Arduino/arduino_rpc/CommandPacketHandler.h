#ifndef ___COMMAND_PACKET_HANDLER__H___
#define ___COMMAND_PACKET_HANDLER__H___


#include "PacketWriter.h"


/* # `process_packet` # */
template <typename Packet, typename Processor>
void process_packet_with_processor(Packet &packet, Processor &processor) {
    uint16_t payload_bytes_to_process = packet.payload_length_;
    if (packet.type() == Packet::packet_type::DATA &&
        payload_bytes_to_process > 0) {
      int result = processor.process_command(packet.payload_length_,
                                             packet.buffer_size_,
                                             packet.payload_buffer_);
      if (result < 0) {
        /* There was an error encountered while processing the request. */
        packet.type(Packet::packet_type::NACK);
        packet.payload_length_ = 0;
      } else {
        packet.payload_length_ = result;
      }
    }
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
    process_packet_with_processor(packet, command_processor_);
    write_packet(ostream_, packet);
  }
};


#endif  // #ifndef ___COMMAND_PACKET_HANDLER__H___
