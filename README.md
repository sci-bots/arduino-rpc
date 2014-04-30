# `simple_rpc` #

This project demonstrates a simple RPC interface to an Arduino device using
methods that are automatically registered by a proxy class using command
meta-data from Protocol buffer message definitions.


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
