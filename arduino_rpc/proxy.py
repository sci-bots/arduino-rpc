import numpy as np
from nadamq.NadaMq import cPacketParser


class ProxyBase(object):
    def _send_command(self, packet):
        self._serial.write(packet.tostring())
        parser = cPacketParser()
        result = None

        while True:
            response = self._serial.read(self._serial.inWaiting())
            if response == '':
                continue
            result = parser.parse(np.fromstring(response, dtype='uint8'))
            if parser.message_completed:
                break
            elif parser.error:
                raise IOError('Error parsing.')
        return result
