# `blink` #

This project demonstrates how an Arduino sketch may be distributed as a Python package.

## Programming sketch using `arduino_helpers` and `avr_helpers` ##

Although not strict dependencies of the `blink` package, by using
`arduino_helpers` and `avr_helpers`, we can easily flash the compiled `.hex`
firmware files included in the `blink` package.

For example:

    >>> import blink
    >>> board = 'diecimila'
    >>> firmware = blink.get_firmwares()[board][0]
    >>> firmware.name
    path('blink.hex')
    >>> from arduino_helpers.context import ArduinoContext, Board, Uploader
    >>> # For Ubuntu systems, Arduino IDE is installed at `/usr/share/arduino`.
    >>> context = ArduinoContext('/usr/share/arduino')
    >>> uploader = Uploader(Board(context, board))
    >>> from avr_helpers import AvrDude
    >>> # Automatically select port, by iterating through available serial
    >>> # ports until a connection can be established.
    >>> avr_dude = AvrDude(uploader.protocol, uploader.board_context.mcu, uploader.speed)
    >>> stdout, stderr = avr_dude.flash(firmware, ['-D'])
    >>> print stderr

    avrdude-x64: AVR device initialized and ready to accept instructions

    Reading | ################################################## | 100% 0.00s

    avrdude-x64: Device signature = 0x1e9406
    avrdude-x64: reading input file "blink.hex"
    avrdude-x64: writing flash (1056 bytes):

    Writing | ################################################## | 100% 0.76s

    avrdude-x64: 1056 bytes of flash written
    avrdude-x64: verifying flash memory against blink.hex:
    avrdude-x64: load data flash data from input file blink.hex:
    avrdude-x64: input file blink.hex contains 1056 bytes
    avrdude-x64: reading on-chip flash data:

    Reading | ################################################## | 100% 0.67s

    avrdude-x64: verifying ...
    avrdude-x64: 1056 bytes of flash verified

    avrdude-x64 done.  Thank you.
