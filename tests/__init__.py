import numpy as np
from nose.tools import ok_, eq_
import serial_device
from arduino_rpc.board import ArduinoRPCBoard


def test_arduino_rpc():
    board_port = list(serial_device.get_serial_ports())[0]
    board = ArduinoRPCBoard(port=board_port)

    yield _test_millis, board
    yield _test_i2c_address, board

    for pin in range(3, 14):
        for value in (0, 1, 0):
            yield _test_digital_pin, board, pin, value
        yield _test_pin_state, board, pin

    yield _test_str_demo, board, 'hello'
    yield _test_echo_array, board, range(5)
    max_int32 = (1 << (32 - 1)) - 1
    yield _test_echo_array, board, (np.linspace(0, max_int32, num=5)
                                    .astype(int).tolist())
    yield _test_echo_array, board, (np.linspace(0, max_int32, num=5)
                                    .astype(int).tolist())[::-1]
    yield _test_str_echo, board, 'hello'


def _test_str_echo(board, value):
    # TODO: This test currently fails.
    eq_(board.str_echo(msg=value), value)


def _test_str_demo(board, value):
    eq_(board.str_demo(), value)


def _test_millis(board):
    time_a = board.get_millis()
    time_b = board.get_millis()
    ok_(time_a < time_b)


def _test_digital_pin(board, pin, value):
    board.pin_mode(pin=pin, mode=1)
    board.digital_write(pin=pin, value=value)
    eq_(board.digital_read(pin=pin), value)


def _test_i2c_address(board):
    i2c_address = board.i2c_address()
    board.set_i2c_address(address=i2c_address)
    eq_(board.i2c_address(), i2c_address)


def _test_echo_array(board, array):
    eq_(board.echo_array(array=array), array)


def _test_pin_state(board, pin_id):
    from arduino_rpc.protobuf_custom import PinState

    # First, read the current state of the pin.
    p = PinState.FromString(board.pin_state(pin_id=pin_id))
    eq_(p.pin_id, pin_id)
    ok_(hasattr(p, 'state'))
    original_state = p.state

    # Toggle the pin state, and read the pin state again.
    board.digital_write(pin=pin_id, value=not original_state)
    p = PinState.FromString(board.pin_state(pin_id=pin_id))
    eq_(p.pin_id, pin_id)
    eq_(p.state, not original_state)

    # Set the pin to its original state.
    board.digital_write(pin=pin_id, value=original_state)
    p = PinState.FromString(board.pin_state(pin_id=pin_id))
    eq_(p.pin_id, pin_id)
    eq_(p.state, original_state)
