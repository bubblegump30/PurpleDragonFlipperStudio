"""Local IR validation; device capability and target response require separate checks."""
from .ir_protocol import signal_command
def inspect_ir(text):
    if not isinstance(text,str) or len(text.encode('utf-8'))>1000000:
        raise ValueError('IR files are limited to 1 MB.')
    headers = {}
    entries = []
    current = None
    warnings = []
    for number, line in enumerate(text.splitlines()):
        line = line.strip()
        if not line or line.startswith('#'): continue
        if ':' not in line:
            warnings.append(f'Line {number + 1}: expected a field and colon.')
            continue
        key, value = (part.strip() for part in line.split(':', 1))
        if key == 'name':
            current = {'name': value, 'line': number, 'fields': {}}
            entries.append(current)
            if len(entries)>512: raise ValueError('IR files are limited to 512 signals.')
        elif current is None:
            if key in headers: warnings.append(f'Line {number + 1}: duplicate header {key}.')
            headers[key] = value
        else:
            if key in current['fields']:
                warnings.append(f'Line {number + 1}: duplicate field {key}.')
                current['duplicates']=True
            current['fields'][key] = value
    if headers.get('Filetype') not in ('IR signals file', 'IR library file'):
        warnings.append('Unrecognized or missing IR file header.')
    if headers.get('Version') != '1': warnings.append('Unsupported or missing version; expected 1.')
    if not entries: warnings.append('No named signals found.')
    names=set()
    for entry in entries:
        if entry['name'].casefold() in names: warnings.append('Duplicate signal name: ' + entry['name'])
        names.add(entry['name'].casefold())
        fields = entry['fields']
        kind = fields.get('type')
        required = {'parsed': ['protocol', 'address', 'command'], 'raw': ['frequency', 'duty_cycle', 'data']}.get(kind)
        if not entry['name']: warnings.append('Signal has an empty name.')
        if required is None: warnings.append(f"{entry['name']}: missing or unsupported signal type.")
        else:
            missing = [key for key in required if not fields.get(key)]
            if missing: warnings.append(f"{entry['name']}: missing {', '.join(missing)}.")
        try: signal_command(entry, for_cli=False)
        except ValueError as exc: warnings.append(entry['name'] + ': ' + str(exc))
    return entries, warnings
