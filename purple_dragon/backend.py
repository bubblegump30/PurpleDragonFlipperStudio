"""Serial transport and extension boundary; no automatic hardware commands."""
import copy
import queue
import codecs
import time
import threading
from .sd_protocol import StorageClient
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
    storage_result = Signal(dict)
    storage_progress = Signal(int, int)

    def __init__(self, port, baud, parent=None):
        super().__init__(parent)
        self.stop_requested = threading.Event()
        self.port, self.baud = port, baud
        self.outbox = queue.Queue(maxsize=32)
        self.query_lock = threading.Lock()
        self.query_pending = False
        self.gpio_state = {}

    def requestInterruption(self):
        self.stop_requested.set()
        super().requestInterruption()

    def isInterruptionRequested(self):
        return self.stop_requested.is_set() or super().isInterruptionRequested()

    def send(self, text):
        with self.query_lock:
            if self.query_pending or self.isInterruptionRequested():
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

    def request_storage(self, operation, path, local=None):
        with self.query_lock:
            if self.query_pending or not self.outbox.empty() or self.isInterruptionRequested():
                return False
            request={'operation': operation, 'path': path, 'local': copy.deepcopy(local)}
            self.outbox.put_nowait(request)
            self.query_pending = True
            return True

    def storage_operation(self, stream, request):
        client = StorageClient(stream, self.isInterruptionRequested, self.storage_progress.emit)
        client.gpio_state = self.gpio_state
        result_payload = None
        try:
            result = client.execute(request['operation'], request['path'], request['local'])
            result_payload = {'ok': True, **request, **result}
        except (ValueError, OSError, UnicodeError, KeyError, TypeError) as exc:
            message = str(exc)
            if client.staged:
                message += ' Staged upload may remain at ' + client.staged + '.'
            result_payload = {'ok': False, **request, 'error': message}
            # A timeout/cancel can leave binary input pending: never resume text on this session.
            self.requestInterruption()
        finally:
            with self.query_lock:
                self.query_pending = False
        self.storage_result.emit(result_payload)

    def query_device_info(self, stream, decoder, timeout=4.0):
        response = ''
        result_payload = None
        try:
            if self.isInterruptionRequested():
                raise ValueError('Device query cancelled.')
            # Preserve buffered incoming console text before issuing the explicit query.
            waiting = stream.in_waiting
            if waiting > MAX_RESPONSE:
                raise ValueError('Serial input is busy. Wait for output to settle and retry.')
            if waiting:
                self.received.emit(decoder.decode(stream.read(waiting)))
            self.gpio_state.clear()
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
                    try:
                        parse_device_info(response)
                    except ValueError as exc:
                        # A complete, bounded identity reply is synchronized enough for
                        # the console. Reject capabilities without closing USB serial.
                        result_payload={'ok':False,'recoverable':True,'error':str(exc)}
                    else:
                        result_payload = {'ok': True, 'response': response}
                    return
            raise ValueError('Device query cancelled.' if self.isInterruptionRequested() else
                             'Device query timed out. Check CLI mode and firmware compatibility, then retry.')
        except (ValueError, OSError) as exc:
            self.requestInterruption()
            result_payload = {'ok': False, 'error': str(exc) + ' Reconnect before querying again.'}
        finally:
            with self.query_lock:
                self.query_pending = False
            if result_payload is not None:
                self.device_info_result.emit(result_payload)

    def run(self):
        if self.isInterruptionRequested():
            self.closed.emit()
            return
        decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')
        try:
            with serial.Serial(self.port, self.baud, timeout=.1, write_timeout=.5) as stream:
                if not self.isInterruptionRequested():
                    self.opened.emit()
                while not self.isInterruptionRequested():
                    try:
                        payload = self.outbox.get_nowait()
                        if isinstance(payload, dict):
                            self.storage_operation(stream, payload)
                        elif payload is None:
                            self.query_device_info(stream, decoder)
                        else:
                            self.gpio_state.clear()
                            stream.write(payload)
                    except queue.Empty:
                        pass
                    if self.isInterruptionRequested():
                        break
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
