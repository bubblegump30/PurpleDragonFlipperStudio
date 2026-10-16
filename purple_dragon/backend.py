"""Serial transport and extension boundary; no automatic hardware commands."""
import queue
import codecs
import time
import threading
from .device_protocol import MAX_RESPONSE, response_complete, parse_device_info
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
    device_info_result = Signal(dict)

    def __init__(self, port, baud, parent=None):
        super().__init__(parent)
        self.port, self.baud = port, baud
        self.outbox = queue.Queue(maxsize=32)
        self.query_lock = threading.Lock()
        self.query_pending = False

    def send(self, text):
        with self.query_lock:
            if self.query_pending:
                return False
            try:
                self.outbox.put_nowait(text.encode('utf-8'))
                return True
            except queue.Full:
                return False

    def request_device_info(self):
        with self.query_lock:
            if self.query_pending or not self.outbox.empty() or self.isInterruptionRequested():
                return False
            self.query_pending = True
            self.outbox.put_nowait(None)
            return True

    def query_device_info(self, stream, decoder, timeout=4.0):
        response = ''
        try:
            if self.isInterruptionRequested():
                raise ValueError('Device query cancelled.')
            # Preserve buffered incoming console text before issuing the explicit query.
            waiting = stream.in_waiting
            if waiting > MAX_RESPONSE:
                raise ValueError('Serial input is busy. Wait for output to settle and retry.')
            if waiting:
                self.received.emit(decoder.decode(stream.read(waiting)))
            stream.write(b'device_info\r')
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline and not self.isInterruptionRequested():
                data = stream.read(min(max(stream.in_waiting, 1), 4096))
                if not data:
                    continue
                text = decoder.decode(data)
                self.received.emit(text)
                response += text
                if len(response) > MAX_RESPONSE:
                    raise ValueError('Device information exceeded the response limit.')
                if response_complete(response):
                    parse_device_info(response)
                    self.device_info_result.emit({'ok': True, 'response': response})
                    return
            raise ValueError('Device query cancelled.' if self.isInterruptionRequested() else
                             'Device query timed out. Check CLI mode and firmware compatibility, then retry.')
        except ValueError as exc:
            self.device_info_result.emit({'ok': False, 'error': str(exc)})
        finally:
            with self.query_lock:
                self.query_pending = False

    def run(self):
        decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')
        try:
            with serial.Serial(self.port, self.baud, timeout=.1, write_timeout=.5) as stream:
                if not self.isInterruptionRequested():
                    self.opened.emit()
                while not self.isInterruptionRequested():
                    try:
                        payload = self.outbox.get_nowait()
                        if payload is None:
                            self.query_device_info(stream, decoder)
                        else:
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
