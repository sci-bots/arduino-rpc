# arduino_rpc #

This package provides code generation for memory-efficient
remote-procedure-calls between a host CPU (Python) and a device (C++) (e.g.,
Arduino).

The main features of this package include:

 - Extract method signatures from class of type `T`.
 - Assign a unique *"command code"* to each method.
 - Generate a `CommandProcessor<T>` C++ class, which calls appropriate method
   on type `T` provided the corresponding serialized command array.
 - Generate a `Proxy` Python class to call methods on remote device by
   serializing Python method call as command request and decoding command
   response from device as Python type(s).

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

## Python ##

 - Assign a unique *"command code"* to each method.
 - Generate a `Proxy` Python class:
   * One method for each "command".  Each method does the following operations:
     - Serialize method arguments and command code to command array.
     - Send serialized command to remote device.
     - Decode device response into Python types.
     - Return decoded result.

## C++ ##

 - Generate a `CommandProcessor<T>` C++ class with the following method:

       UInt8Array process_command(UInt8Array request_arr, UInt8Array buffer)

   * `process_command` arguments:
     - `request_arr`: Serialized command request structure array.
     - `buffer`: Buffer array (available for writing output).
   * `CommandProcessor<T>` is constructed with reference to instance of object
     of type `T`.
   * The `process_command` method decodes the command and arguments from the
     `request_arr` and calls the corresponding method on the `T` instance
     (passing in the decoded arguments).  The return value of the method is
     written to the output `buffer` array.


# Author #

Copyright 2015 Christian Fobel <christian@fobel.net>
