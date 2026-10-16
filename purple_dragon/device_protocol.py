"""Read-only official CLI device_info adapter. Protocol checks are not authentication."""
import re

MAX_RESPONSE = 65536
ANSI = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')
FIELDS = ('hardware_model', 'hardware_name', 'hardware_uid', 'hardware_target',
          'firmware_version', 'firmware_commit', 'firmware_branch',
          'firmware_build_date', 'firmware_api_major', 'firmware_api_minor',
          'protobuf_version_major', 'protobuf_version_minor')


def parse_device_info(text):
    if not isinstance(text,str):
        raise ValueError('Device information must be text.')
    if len(text) > MAX_RESPONSE:
        raise ValueError('Device information exceeded the response limit.')
    values = {}
    for line in ANSI.sub('', text).splitlines():
        match = re.fullmatch(r'\s*([a-z][a-z0-9_]{0,63})\s*:\s*([^\x00-\x1f]{1,256})\s*', line)
        if match:
            key, value = match.group(1), match.group(2).strip()
            if key in values:
                raise ValueError('Ambiguous duplicate device information fields.')
            values[key] = value
    if values.get('device_info_major') != '2':
        raise ValueError('Unsupported or missing device_info format (expected major 2).')
    if values.get('hardware_model', '').replace(' ', '').lower() != 'flipperzero':
        raise ValueError('The response does not identify a Flipper Zero model.')
    if values.get('hardware_target') != '7' or not re.fullmatch(r'[0-9A-Fa-f]{24}', values.get('hardware_uid', '')):
        raise ValueError('Missing or incompatible Flipper hardware identity fields.')
    if not values.get('firmware_version') or not values.get('firmware_commit'):
        raise ValueError('Incomplete firmware information.')
    if not all(re.fullmatch(r'\d{1,5}', values.get(k, '')) for k in ('protobuf_version_major', 'protobuf_version_minor')):
        raise ValueError('Incomplete device information response.')
    return {key: values[key] for key in FIELDS if key in values}


def response_complete(text):
    # Official furi_hal_info_get emits protobuf_version_minor as its final field.
    clean = ANSI.sub('', text)
    return bool(re.search(r'(?:^|\n)protobuf_version_minor\s*:\s*\d+\s*\r?\n', clean))


class DeviceInfoAdapter:
    """Connection-scoped capability state. Never infer GPIO/storage support from a CLI."""
    def __init__(self):
        self.reset()

    def reset(self):
        self.state = 'unverified'
        self.capabilities = frozenset()
        self.info = {}
        self.error = ''

    def begin(self):
        self.reset()
        self.state = 'querying'

    def complete(self, result):
        self.reset()
        if not isinstance(result,dict):
            self.state='unsupported';self.error='Invalid device query result.';return
        if result.get('ok'):
            # Validate again at the adapter boundary rather than trust arbitrary signal data.
            try:
                self.info = parse_device_info(result['response'])
                self.state = 'identified'
                self.capabilities = frozenset({'device_info'})
            except (ValueError, KeyError, TypeError) as exc:
                self.state = 'unsupported'
                self.error = str(exc)
        else:
            self.state = 'unsupported'
            self.error = result.get('error', 'Device information query failed.')
