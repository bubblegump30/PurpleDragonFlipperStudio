"""Serial transport and extension boundary; no automatic hardware commands."""
import queue
import codecs
from PySide6.QtCore import QThread, Signal
import serial
from serial.tools import list_ports


def discover_ports():
    return sorted(list_ports.comports(), key=lambda p: p.device)


class SerialSession(QThread):
    opened = Signal()
    received = Signal(str)
    fault = Signal(str)
    closed = Signal()

    def __init__(self, port, baud, parent=None):
        super().__init__(parent)
        self.port, self.baud = port, baud
        self.outbox = queue.Queue(maxsize=32)

    def send(self, text):
        try:
            self.outbox.put_nowait(text.encode('utf-8'))
            return True
        except queue.Full:
            return False

    def run(self):
        decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')
        try:
            with serial.Serial(self.port, self.baud, timeout=.1, write_timeout=.5) as stream:
                if not self.isInterruptionRequested():
                    self.opened.emit()
                while not self.isInterruptionRequested():
                    try:
                        payload = self.outbox.get_nowait()
                        stream.write(payload)
                    except queue.Empty:
                        pass
                    data = stream.read(min(max(stream.in_waiting, 1), 4096))
                    if data:
                        self.received.emit(decoder.decode(data))
        except (serial.SerialException, OSError, ValueError) as exc:
            self.fault.emit(str(exc))
        finally:
            self.closed.emit()


class HardwareAdapter:
    """Override to integrate the existing RC7 device services.

    Keep application protocol logic here rather than in view handlers.
    Run blocking operations in a worker and deliver results with Qt signals.
    The base adapter intentionally exposes no hardware capabilities.
    """
    capabilities = frozenset()

    def gpio(self, pin, action):
        raise NotImplementedError('Connect the RC7 GPIO backend first.')

    def backup(self, destination):
        raise NotImplementedError('Connect the RC7 backup backend first.')

    def transmit_ir(self, signal):
        raise NotImplementedError('Connect the RC7 IR backend first.')
