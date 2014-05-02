#ifndef ___PACKET_HANDLER__H___
#define ___PACKET_HANDLER__H___

#include "output_buffer.h"
#include "PacketHandler.h"
#include "PacketParser.h"


template <typename Parser, typename IStream, typename Handler>
class PacketReactor : public PacketHandlerBase<Parser, IStream> {
  /* # `PacketReactor` #
   *
   * This class watches for incoming packets on an input stream _(e.g., an
   * Arduino `Serial` stream), and invokes the `process_packet` method of a
   * provided packet-handler on each complete packet received.
   *
   * __NB__ Errors which occur during the parsing of a packet are currently
   * ignored.  Regular operation resumes, such that subsequent valid packets
   * are handled as usual.
   *
   * ## Template arguments ##
   *
   *  - `IStream`: An input stream _(e.g, `Serial`)_, providing the following API:
   *    - `available()`: Return the number of available bytes for reading.
   *    - `read()`: Return the next available byte.
   *  - `Parser`: A parser which parses packets one byte at-a-time through the
   *   following API:
   *    - `parse_byte(uint8_t *byte)`
   *  - `Handler`: A class defining the actions to take when a complete, valid
   *   packet is available.  The handler is invoked through the following API:
   *    - `process_packet(packet_type &packet)`
   *
   * ## Notes ##
   *
   *  - The actual type of the packet is determined by the packet type defined
   *   in the `Parser` class.
   *   - The `Handler::process_packet(...)` method can be templated _(see
   *    `CommandPacketHandler` for example)_ to support processing different
   *    types of packets, as long as they supply the required
   *    attributes/methods. */
  public:

  typedef PacketHandlerBase<Parser, IStream> base_type;
  typedef typename base_type::packet_type packet_type;

  using base_type::parser_;

  Handler &handler_;

  PacketReactor(Parser &parser, IStream &istream, Handler &handler)
    : base_type(parser, istream), handler_(handler) {}

  virtual void handle_packet(packet_type &packet) {
    /* ## `handle_packet` ##
     *
     * This method is called whenever a complete packet has been parsed
     * successfully from the input-stream. */
    handler_.process_packet(packet);
  }

  virtual void handle_error(packet_type &packet) {}
};


#endif  // #ifndef ___PACKET_HANDLER__H___
