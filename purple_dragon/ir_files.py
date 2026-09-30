"""Local IR structure inspection; never transmits or certifies device compatibility."""
def inspect_ir(text):
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
        elif current is None:
            headers[key] = value
        else:
            if key in current['fields']:
                warnings.append(f'Line {number + 1}: duplicate field {key}.')
            current['fields'][key] = value
    if headers.get('Filetype') not in ('IR signals file', 'IR library file'):
        warnings.append('Unrecognized or missing IR file header.')
    if headers.get('Version') != '1': warnings.append('Unsupported or missing version; expected 1.')
    if not entries: warnings.append('No named signals found.')
    for entry in entries:
        fields = entry['fields']
        kind = fields.get('type')
        required = {'parsed': ['protocol', 'address', 'command'], 'raw': ['frequency', 'duty_cycle', 'data']}.get(kind)
        if not entry['name']: warnings.append('Signal has an empty name.')
        if required is None: warnings.append(f"{entry['name']}: missing or unsupported signal type.")
        else:
            missing = [key for key in required if not fields.get(key)]
            if missing: warnings.append(f"{entry['name']}: missing {', '.join(missing)}.")
    return entries, warnings
