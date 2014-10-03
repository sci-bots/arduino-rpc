from nose.tools import ok_, eq_
import serial_device
from arduino_rpc.board import ArduinoRPCBoard


def test_arduino_rpc():
    board_port = list(serial_device.get_serial_ports())[0]
    board = ArduinoRPCBoard(port=board_port)

    yield _test_millis, board

    for pin in range(2, 14):
        for value in (0, 1):
            yield _test_digital_pin, board, pin, value

    yield _test_str_echo, board, 'hello'


def _test_str_echo(board, value):
    eq_(board.str_echo(msg=value), value)


def _test_millis(board):
    time_a = board.get_millis()
    time_b = board.get_millis()
    ok_(time_a < time_b)


def _test_digital_pin(board, pin, value):
    board.pin_mode(pin=pin, mode=1)
    board.digital_write(pin=pin, value=value)
    eq_(board.digital_read(pin=pin), value)
