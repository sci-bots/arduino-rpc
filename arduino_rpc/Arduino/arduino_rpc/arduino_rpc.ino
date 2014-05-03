#include "Memory.h"
#include "PacketParser.h"
#include "CommandPacketHandler.h"
#include "NodeCommandProcessor.h"
#include "packet_handler.h"


#define PACKET_SIZE   128
uint8_t packet_buffer[PACKET_SIZE];

typedef CommandPacketHandler<Stream, CommandProcessor> Handler;
typedef PacketReactor<PacketParser<FixedPacket>, Stream, Handler> Reactor;

Node node;
CommandProcessor command_processor(node);
FixedPacket packet;
/* `reactor` maintains parse state for a packet, and updates state one-byte
 * at-a-time. */
PacketParser<FixedPacket> parser;
/* `handler` processes complete packets and sends response as necessary. */
Handler handler(Serial, command_processor);
/* `reactor` uses `parser` to parse packets from input stream and passes
 * complete packets to `handler` for processing. */
Reactor reactor(parser, Serial, handler);

void setup() {
  packet.reset_buffer(PACKET_SIZE, &packet_buffer[0]);
  parser.reset(&packet);
  Serial.begin(115200);
}

void loop() {
  /* Parse all new bytes that are available.  If the parsed bytes result in a
   * completed packet, pass the complete packet to the command-processor to
   * process the request. */
  reactor.parse_available();
}
