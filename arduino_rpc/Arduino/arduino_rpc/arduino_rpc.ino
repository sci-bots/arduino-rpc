#include "EEPROM.h"
#include "Wire.h"
#include "Memory.h"
#include "PacketParser.h"
#include "Node.h"
#include "CommandPacketHandler.h"
#include "NodeCommandProcessor.h"
#include "packet_handler.h"


#define PACKET_SIZE   28
/* To save RAM, the serial-port interface may be disabled by defining
 * `DISABLE_SERIAL`. */
#ifndef DISABLE_SERIAL
uint8_t packet_buffer[PACKET_SIZE];
#endif  // #ifndef DISABLE_SERIAL

uint8_t i2c_packet_buffer[PACKET_SIZE];
uint8_t processing_i2c_request = false;
uint8_t i2c_response_size_sent = false;
FixedPacket i2c_packet;

Node node;
CommandProcessor<Node> command_processor(node);

#ifndef DISABLE_SERIAL
typedef CommandPacketHandler<Stream, CommandProcessor<Node> > Handler;
typedef PacketReactor<PacketParser<FixedPacket>, Stream, Handler> Reactor;

FixedPacket packet;
/* `reactor` maintains parse state for a packet, and updates state one-byte
 * at-a-time. */
PacketParser<FixedPacket> parser;
/* `handler` processes complete packets and sends response as necessary. */
Handler handler(Serial, command_processor);
/* `reactor` uses `parser` to parse packets from input stream and passes
 * complete packets to `handler` for processing. */
Reactor reactor(parser, Serial, handler);
#endif  // #ifndef DISABLE_SERIAL


void setup() {
#ifdef __AVR_ATmega2560__
  /* Join I2C bus as master. */
  Wire.begin();
#else
  /* Join I2C bus as slave. */
  Wire.onReceive(i2c_receive_event);
  Wire.onRequest(i2c_request_event);
#endif  // #ifdef __AVR_ATmega328__
  // Set i2c clock-rate to 400kHz.
  TWBR = 12;
#if !defined(DISABLE_SERIAL)
  Serial.begin(115200);
  packet.reset_buffer(PACKET_SIZE, &packet_buffer[0]);
  parser.reset(&packet);
#endif  // #ifndef DISABLE_SERIAL
  i2c_packet.reset_buffer(PACKET_SIZE, &i2c_packet_buffer[0]);
}


void loop() {
#ifndef DISABLE_SERIAL
  /* Parse all new bytes that are available.  If the parsed bytes result in a
   * completed packet, pass the complete packet to the command-processor to
   * process the request. */
  reactor.parse_available();
#endif  // #ifndef DISABLE_SERIAL
  if (processing_i2c_request) {
    process_packet_with_processor(i2c_packet, command_processor);
    processing_i2c_request = false;
  }
}


void i2c_receive_event(int byte_count) {
  processing_i2c_request = true;
  /* Record all bytes received on the i2c bus to a buffer.  The contents of
   * this buffer will be forwarded to the local serial-stream. */
  int i;
  for (i = 0; i < byte_count; i++) {
      i2c_packet_buffer[i] = Wire.read();
  }
  i2c_packet.payload_length_ = i;
  i2c_packet.type(Packet::packet_type::DATA);
}


void i2c_request_event() {
  uint8_t byte_count = (uint8_t)i2c_packet.payload_length_;
  /* There is a response from a previously received packet, so send it to the
   * master of the i2c bus. */
  if (!i2c_response_size_sent) {
    if (processing_i2c_request) {
      Wire.write(0xFF);
    } else {
      Wire.write(byte_count);
      i2c_response_size_sent = true;
    }
  } else {
    Wire.write(i2c_packet.payload_buffer_, byte_count);
    i2c_response_size_sent = false;
  }
}
