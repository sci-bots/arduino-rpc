from arduino_helpers.context import (auto_context, Board, Uploader,
                                     ArduinoContext)
from serial_device import get_serial_ports
from . import get_firmwares


def upload_firmware(firmware_path, board_name, port=None,
                    arduino_install_home=None):
    '''
    Upload the specified firmware file to the specified board.
    '''
    if arduino_install_home is None:
        context = auto_context()
    else:
        context = ArduinoContext(arduino_install_home)
    board = Board(context, board_name)
    uploader = Uploader(board)
    available_ports = list(get_serial_ports())
    if port is None:
        # No serial port was specified.
        if len(available_ports) == 1:
            # There is only one serial port available, so select it
            # automatically.
            port = available_ports[0]
        else:
            raise IOError('No serial port was specified.  Please select one of'
                          ' the following ports: %s' % available_ports)
    uploader.upload(firmware_path, port)


def upload(board_name, port=None, arduino_install_home=None):
    '''
    Upload the first firmware that matches the specified board type.
    '''
    firmware_path = get_firmwares()[board_name][0]
    upload_firmware(firmware_path, board_name, port, arduino_install_home)
