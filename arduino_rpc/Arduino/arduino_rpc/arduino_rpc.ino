#include "Wire.h"
#include "Memory.h"
#include "PacketParser.h"
#include "Node.h"
#include "CommandPacketHandler.h"
//#include "NodeCommandProcessor.h"
/* TODO: Re-enable `NodeCommandProcessor.h` include.
 * TODO: Modify `NodeCommandProcessor.h` code-generator template to include
 * request I2C forwarding.
 *  - This also requires an update to the protocol buffer generation to include
 *    the `ForwardI2cRequest` message types.
 *
 * __Temporarily__ disable include to prototype array argument handling through
 * Protocol Buffer RPC interface.  This will enable, among other things, acting
 * as a bridge between a serial connection and an i2c bus. */
#include "CommandProcessor.h"
#include "packet_handler.h"

#ifndef __AVR_ATmega2560__
/* Disable serial port communications to save RAM unless we are compiling for
 * the Mega2560, which has much more RAM to spare. */
#define DISABLE_SERIAL
#endif  // #ifndef __AVR_ATmega2560__


#define PACKET_SIZE   28
#ifndef DISABLE_SERIAL
uint8_t packet_buffer[PACKET_SIZE];
#endif  // #ifndef DISABLE_SERIAL

uint8_t i2c_packet_buffer[PACKET_SIZE];
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
  Wire.begin(0x10);
  Wire.onReceive(i2c_receive_event);
  Wire.onRequest(i2c_request_event);
#endif  // #ifdef __AVR_ATmega328__
  // Set i2c clock-rate to 400kHz.
  TWBR = 12;
#ifndef DISABLE_SERIAL
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
}


void i2c_receive_event(int byte_count) {
  /* Record all bytes received on the i2c bus to a buffer.  The contents of
   * this buffer will be forwarded to the local serial-stream. */
  int i;
#ifdef DEBUG_I2C
  Serial.println("r");
#endif  // DEBUG_I2C
  if (Wire.available() > 0) {
#ifdef DEBUG_I2C
      Serial.println(Wire.available());
#endif  // DEBUG_I2C
      uint8_t bytes_read = Wire.available();
      for (i = 0; i < bytes_read; i++) {
          i2c_packet_buffer[i] = Wire.read();
#ifdef DEBUG_I2C
          Serial.print((uint16_t)i2c_packet_buffer[i]);
          Serial.print(",");
#endif  // DEBUG_I2C
      }
#ifdef DEBUG_I2C
      Serial.println("");
#endif  // DEBUG_I2C
      i2c_packet.payload_length_ = i;
      i2c_packet.type(Packet::packet_type::DATA);
  }
#ifdef DEBUG_I2C
  Serial.println("d");
#endif  // DEBUG_I2C
  process_packet_with_processor(i2c_packet, command_processor);
}


void i2c_request_event() {
#ifdef DEBUG_I2C
  Serial.println("q");
#endif  // DEBUG_I2C
  /* There is a response from a previously received packet, so send it to the
   * master of the i2c bus. */
  if (!i2c_response_size_sent) {
#ifdef DEBUG_I2C
    Serial.println(i2c_packet.payload_length_);
#endif  // DEBUG_I2C
    Wire.write((uint8_t)i2c_packet.payload_length_);
    i2c_response_size_sent = true;
  } else {
    Wire.write(i2c_packet.payload_buffer_, i2c_packet.payload_length_);
    i2c_response_size_sent = false;
#ifdef DEBUG_I2C
    for (int i = 0; i < i2c_packet.payload_length_; i++) {
        Serial.print((uint16_t)i2c_packet_buffer[i]);
        Serial.print(",");
    }
    Serial.println("");
#endif  // DEBUG_I2C
  }
#ifdef DEBUG_I2C
  Serial.println("D");
#endif  // DEBUG_I2C
}
