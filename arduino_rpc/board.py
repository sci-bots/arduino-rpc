import time

from nadamq.command_proxy import (NodeProxy, RemoteNodeProxy,
                                  CommandRequestManager,
                                  CommandRequestManagerDebug, SerialStream)
from arduino_rpc.requests import (REQUEST_TYPES, CommandResponse,
                                  CommandRequest, CommandType)


class ArduinoRPCBoard(NodeProxy):
    def __init__(self, port, baudrate=115200, debug=False):
        if not debug:
            request_manager = CommandRequestManager(REQUEST_TYPES,
                                                    CommandRequest,
                                                    CommandResponse,
                                                    CommandType)
        else:
            request_manager = CommandRequestManagerDebug(REQUEST_TYPES,
                                                         CommandRequest,
                                                         CommandResponse,
                                                         CommandType)
        stream = SerialStream(port, baudrate=baudrate)
        super(ArduinoRPCBoard, self).__init__(request_manager, stream)
        self._stream._serial.setDTR(False)
        time.sleep(0.5)
        self._stream._serial.setDTR(True)
        time.sleep(1)
        print 'free memory:', self.ram_free()


class RemoteArduinoRPCBoard(RemoteNodeProxy):
    def __init__(self, forward_proxy, remote_address, debug=False,
                 timeout=None):
        if not debug:
            request_manager = CommandRequestManager(REQUEST_TYPES,
                                                    CommandRequest,
                                                    CommandResponse,
                                                    CommandType)
        else:
            request_manager = CommandRequestManagerDebug(REQUEST_TYPES,
                                                         CommandRequest,
                                                         CommandResponse,
                                                         CommandType)
        super(RemoteArduinoRPCBoard, self).__init__(forward_proxy,
                                                    remote_address,
                                                    request_manager)
