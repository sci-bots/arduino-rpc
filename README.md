# `simple_rpc` #

This project demonstrates a simple RPC interface to an Arduino device using
methods that are automatically registered by a proxy class using command
meta-data from [Protocol buffer][1] message definitions.


# API Example #

Below, we show an example session interacting with the Arduino device through a
serial stream.  Note that the `NodeProxy` is a generic class from the `nadamq`
module, and that all `simple_rpc`-specific code is based entirely off of the
Protocol Buffer definitions and the corresponding auto-generated Python message
classes.

    >>> from nadamq.command_proxy import (NodeProxy, CommandRequestManager,
    ...                                   SerialStream)
    >>> from simple_rpc.requests import (REQUEST_TYPES, CommandResponse,
    ...                                  CommandRequest, CommandType)
    >>> stream = SerialStream(‘/dev/ttyUSB0’, baudrate=115200)
    >>> n = NodeProxy(CommandRequestManager(REQUEST_TYPES, CommandRequest,
    ...                                     CommandResponse, CommandType),
    ...               stream)
    >>> n.
    n.echo            n.led_on          n.ram_bss_size    n.ram_free        n.ram_size
    n.led_off         n.led_state       n.ram_data_size   n.ram_heap_size   n.ram_stack_size
    >>> n.ram_free()
    6445
    >>> n.ram_size()
    8191
    >>> n.led
    n.led_off    n.led_on     n.led_state
    >>> n.led_state()
    False
    >>> n.led_on()
    <simple_rpc.simple_pb2.LEDOnResponse object at 0x7f2871aa4280>
    >>> n.led_state()
    True
    >>> n.led_off()
    <simple_rpc.simple_pb2.LEDOffResponse object at 0x7f2871aa43d0>
    >>> n.led_state()
    False


# What is this?  Why did you make this? #

Much of the effort of coding our own Arduino projects was dedicated:

 - To defining and writing protocols.
 - Writing host code to interface with these project-specific protocols.

There are a few problems with this:

 - Lots of duplicated effort, redefining protocols for every project, or at
   best, copying and pasting and modifying to suit.
 - Brittle code, since any change on the device protocol API required the host
   code to be updated separately to match.
 - More time spent on just getting signals to/from the device than spent on the
   real problem at hand.


## What do we propose? ##

Instead of writing the protocol for every project, we want to abstract the
communication to and from the device as far away as possible from the actual
interface connection _(e.g., serial, I2C, etc.)_.  The goal is to expose
functions from the device to _a)_ other devices _(e.g., over I2C)_, and _b)_ to
the host computer, without having to care about where the requested function
call is coming from.

To accomplish this we employ automatic code-generation to scan a set of
user-defined functions that should be exposed and create code to call the
functions through:

 - Serial interface.
 - I2C.

Furthermore, we also get Python code to run on the host side to connect to the
device over serial, or to devices on the I2C bus by forwarding requests through
a device connected via serial.

Voila!  No more writing protocols!  Just add functions to your Arduino sketch,
and the protocol will be auto-generated based on the function signatures.

Now for the details...


# How does it work? #

To expose functions on the Arduino to run via RPC, methods are added to a
special `Node` class, defined in the `Node.h` header.  The methods of the
`Node` class act as entry points for the RPC mechanism to the execution context
of the Arduino.

For example, consider the `pin_mode` RPC method, which is available via the RPC
interface of the `arduino_rpc` example project.  Below, we show the relevant
contents of the `Node.h` file, again, which contains the `Node` class
definition.

```C++
    class Node {
    ...
      void pin_mode(uint8_t pin, uint8_t mode) { return pinMode(pin, mode); }
    ...
```

Note that the method is actually just a very simple wrapper around the
`pinMode` function provided by the Arduino core library.


## Code-generation ##

Adding a method such as `pin_mode` to the `Node` class is all that is necessary
to have the following code auto-generated:

 - A [Protocol buffer][1] message type definition for each function signature.
 - Interface stream listeners, each of which listens for incoming requests on a
   particular interface.  For now, the following interfaces are supported:
  * Serial.
  * I2C.
 - A “command-processor”, which:
  1. Decodes each incoming request _(from any of the supported interfaces)_.
  2. Unpacks any supplied arguments.
  3. Calls the corresponding method on the `Node` instance.
  4. Encodes the return type into a [protocol buffer][1] message.
  5. Sends the response back over the interface that it was received on.
 - A Python proxy object that exposes the methods of the `Node` class as local
   methods on the Python object.
  * _Caveat:_ Due to how the requests are currently encoded by the Python proxy
    object, the arguments passed to a Python method call _must be passed as
    keyword arguments_.

### Notes ###

On the Arduino device, the [`nanopb`][2] library is used for encoding/decoding
the protocol buffer messages.

On the host, the standard [Protocol Buffers][1] compiler is used to generate Python code
for the message types in the generated [protocol buffers][1] definitions.  An
instance of the generic `NodeProxy` class then loads the Python protocol buffer code
and dynamically adds a method for each remote method defined.


# Why wouldn’t I want to use this? #

## Run-time overhead ##

There is some additional overhead involved in packing/unpacking [Protocol
Buffer][1] requests and responses.  For _extremely_ time-sensitive code, this
might be unacceptable.  However, in practice, the round-trip response-time from
Python-to-device-to-Python is about 5ms.  For _many_ applications, this should
be sufficiently fast.


## Memory overhead ##

Currently, each method added to the `Node` class adds about 40 bytes of memory
overhead.  This still allows quite a few methods, even on an Arduino Uno, but
we have run up against the memory limit on some of our projects.  However,
there are several ways to address this issue with the current implementation,
and we have [some ideas][2] of how to address this during code generation, as
well.

For now, the easiest option is likely to implement a single method that accepts
two arguments:

 1. A command code.
 2. A byte array.

The method can then use the command code to call a function/method defined
outside of the `Node` class.  Note that the byte array could contain an
arbitrary data-type that can be decoded inside the method to pass the arguments
required for the specified command.  Note that this requires more boiler-plate
code on the Arduino and special-handling on the host, but hopefully this is not
necessary in the majority of cases.


[1]: https://code.google.com/p/protobuf/
[2]: http://koti.kapsi.fi/jpa/nanopb/
[3]: https://github.com/wheeler-microfluidics/arduino_rpc/issues/10
