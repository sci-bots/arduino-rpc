# arduino_rpc #

This package provides code generation for memory-efficient
remote-procedure-calls between a host CPU (Python) and a device (C++) (e.g.,
Arduino).

The main features of this package include:

 - Extract method signatures from user-defined C++ class.
 - Assign a unique *"command code"* to each method.
 - Generate a `CommandProcessor<T>` C++ class, which calls appropriate method
   on instance of user type provided the corresponding serialized command
   array.
 - Generate a `Proxy` Python class to call methods on remote device by
   serializing Python method call as command request and decoding command
   response from device as Python type(s).


# What is this? #

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

Voila!  No more writing protocols!  Just add methods to your class in your
Arduino sketch, and the protocol will be auto-generated based on the function
signatures.


# Extract method signatures #

The code generation mechanism in the `arduino_rpc` package assumes a single,
user-defined C++ class type.  Within the `arduino_rpc` code, the user-defined
class is referred to as the `Node` class (though the class can be named
anything).

## `arduino_rpc.get_multilevel_method_sig_frame` function ##

Given one or more C++ header paths, each with a corresponding C++ class name,
the `get_multilevel_method_sig_frame` function returns a `pandas.DataFrame`
with one row per method argument.

For example, consider the following class:

    // Node.hpp
    #include <stdint.h>

    class Node {
    public:
      uint8_t add(uint8_t a, uint8_t b) { return a + b; }
      uint8_t subtract(uint8_t a, uint8_t b) { return a - b; }
    };

A call to `get_multilevel_method_sig_frame('Node.hpp', 'Node')` would return a
`pandas.DataFrame` containing information about the signatures for methods
`add` and `subtract`.

### Inheritance ###

Inheritance is also supported by the `get_multilevel_method_sig_frame`.

For example, consider the following headers:

    // A.hpp
    #include <stdint.h>

    class A {
    public:
      virtual uint8_t add(uint8_t a, uint8_t b) { return 0; }
      virtual uint8_t divide(uint8_t a, uint8_t b) { return a / b; }
    };

    // B.hpp
    #include <stdint.h>

    class B {
    public:
      virtual uint8_t multiply(uint8_t a, uint8_t b) { return a * b; }
    };

    // Node.hpp
    #include <stdint.h>
    #include "A.hpp"
    #include "B.hpp"

    class Node : public A, public B {
    public:
      uint8_t add(uint8_t a, uint8_t b) { return a + b; }
      uint8_t subtract(uint8_t a, uint8_t b) { return a - b; }
    };

The following call to:

    get_multilevel_method_sig_frame(['A.hpp', 'B.hpp', 'Node.hpp'],  # headers
                                    ['A', 'B', 'Node'])  # class names

would return a `pandas.DataFrame` containing information about the signatures
for methods `A::divide`, `B::multiply`, `Node::add`, and `Node::subtract`.
Note that `Node::add` overrides `A::add`.

### Template class support ###

Note that template classes are also supported.  For example, the class defined as:

   class ClassName<typename Parameter1, typename Parameter2> {...};

is referenced in the frame with the `class_name` of
`ClassName<Parameter1, Parameter2>`.

### Known limitations ###

 - Base classes and corresponding C++ header paths must be specified explicitly.
 - Order of C++ header paths and class names in
   `get_multilevel_method_sig_frame` arguments must match inheritance order.
 - Overloaded methods (i.e., same method name with different number of
   arguments) are currently not supported.


# Code generation #

The `arduino_rpc` package includes functions to serialize/deserialize commands,
where each command corresponds to a method signature extracted as described in
the *"Extract method signatures"* section above.

Given a list of method signatures (see *"Extract method signatures"*), the
basic idea is:

 - Assign a unique *"command code"* to each method.
 - Generate a Python class with one method per command.
 - Generate a C++ class that wraps an instance of the user-defined C++ class,
   and calls a method on the wrapped instance based on a "command code".

## Command flow ##

Each call to a method of a Python `Proxy` instance triggers a remote procedure
call (RPC) to the corresponding method on the wrapped user class instance on
the device.

For example:

       Python (Proxy)                 C++ (CommandProcessor)
       ==============                 ======================

       proxy.add(a, b)

        encode("add",     encoded
               a, b)  ->  command ->  result = wrapper.process_command(array,
                           array                                       buffer)

                          encoded
        decode(result) <-  result <-  encode(result)
                           array
        return result

## Python ##

Generate a `Proxy` Python class with one method for each "command".  Each
method performs the following operations:

 - Serialize method arguments and command code to command array.
 - Send serialized command to remote device.
 - Decode device response into Python types.
 - Return decoded result.

### Usage ###

For example, consider the `Node` class from the inheritance example above.  The
following code would write the Python `Proxy` class to the path specified by
`output_path`.

    from arduino_rpc.code_gen import write_code
    from arduino_rpc.rpc_data_frame import get_python_code

    write_code(['A.hpp', 'B.hpp', 'Node.hpp'],  # headers
               ['A', 'B', 'Node'],  # class names
               output_path,  # output filename
               get_python_code,  # function to map to method signatures frame
               *['-I%s' % include_path])  # path containing headers

## C++ ##

Generate a `CommandProcessor<Node>` C++ class with the following method:

    UInt8Array process_command(UInt8Array request_arr, UInt8Array buffer)

 - `process_command` arguments:
     * `request_arr`: Serialized command request structure array.
     * `buffer`: Buffer array (available for writing output).
 - `CommandProcessor<Node>` is constructed with reference to instance of object
   of type `Node`.
 - The `process_command` method decodes the command and arguments from the
   `request_arr` and calls the corresponding method on the `Node` instance
   (passing in the decoded arguments).  The return value of the method is
   written to the output `buffer` array.

### Usage ###

For example, consider the `Node` class from the inheritance example above.  The
following code would write the C++ `CommandProcessor` wrapper class header to
the path specified by `output_path`.

    from arduino_rpc.code_gen import write_code
    from arduino_rpc.rpc_data_frame import get_c_header_code

    write_code(['A.hpp', 'B.hpp', 'Node.hpp'],  # headers
               ['A', 'B', 'Node'],  # class names
               output_path,  # output filename
               get_c_header_code,  # function to map to method signatures frame
               *['-I%s' % include_path])  # path containing headers


# Projects using `arduino_rpc` #

 - base-node-rpc: Base classes for Arduino RPC node/device.
     * A memory-efficient set of base classes providing an API to most of the
       Arduino API, including EEPROM access, raw I2C
       master-write/slave-request, etc.
     * Support for processing RPC command requests through either serial or I2C
       interface.
     * For more info see [here][1].


# Author #

Copyright 2015 Christian Fobel <christian@fobel.net>


[1]: https://github.com/wheeler-microfluidics/base_node_rpc
