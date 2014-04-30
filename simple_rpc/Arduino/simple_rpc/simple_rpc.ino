#include "Memory.h"
#include "PacketParser.h"
#include "SimpleCommand.h"
#include "packet_handler.h"


uint8_t protobuf[128];
#define PACKET_SIZE   64
uint8_t packet_buffer[PACKET_SIZE];
char output_buffer[128];

typedef CommandPacketHandler<Stream, CommandProcessor> Handler;
typedef PacketReactor<PacketParser<FixedPacket>, Stream, Handler> Reactor;

CommandProcessor command_processor;
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
  reactor.parse_available();
  delay(50);
}
