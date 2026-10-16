"""Validated single-command IR transmission; completion is not target acknowledgement."""
from decimal import Decimal, InvalidOperation
import re
from .sd_protocol import StorageError, PROMPT

PROTOCOL_BITS = {'NEC':(8,8),'NECext':(16,16),'NEC42':(13,8),'NEC42ext':(26,16),
                 'Samsung32':(8,8),'RC6':(8,8),'RC5':(5,6),'RC5X':(5,7),
                 'SIRC':(5,7),'SIRC15':(8,7),'SIRC20':(13,7),'Kaseikyo':(26,10),
                 'RCA':(4,8),'Pioneer':(8,8)}


def signal_command(entry, for_cli=True):
    if not isinstance(entry, dict) or not isinstance(entry.get('fields'), dict):
        raise ValueError('Invalid IR signal.')
    fields = entry['fields']
    if any(not isinstance(v,str) for v in fields.values()): raise ValueError('IR fields must be text.')
    if entry.get('duplicates'): raise ValueError('Duplicate fields make this signal ambiguous.')
    name = entry.get('name')
    if not isinstance(name,str) or not name.strip() or len(name)>120 or any(ord(c)<32 or c in '<>' for c in name):
        raise ValueError('Signal name must be readable text up to 120 characters.')
    if fields.get('type') == 'parsed':
        if set(fields) != {'type','protocol','address','command'}: raise ValueError('Parsed signal fields are missing or unsupported.')
        protocol = fields['protocol']
        if protocol not in PROTOCOL_BITS: raise ValueError('Unsupported parsed protocol.')
        values=[]
        for key,bits in zip(('address','command'),PROTOCOL_BITS[protocol]):
            value=fields[key]
            if not isinstance(value,str) or not re.fullmatch(r'[0-9A-Fa-f]{2}(?:\s+[0-9A-Fa-f]{2}){3}',value):
                raise ValueError(key + ' must contain four hexadecimal bytes.')
            number=int.from_bytes(bytes.fromhex(value),'little')
            if number >= (1<<bits): raise ValueError(key + ' exceeds the protocol bit range.')
            values.append(format(number,'X'))
        command='ir tx ' + protocol + ' ' + ' '.join(values)
    elif fields.get('type') == 'raw':
        if set(fields) != {'type','frequency','duty_cycle','data'}: raise ValueError('Raw signal fields are missing or unsupported.')
        if not isinstance(fields['frequency'],str) or not re.fullmatch(r'\d{1,7}',fields['frequency']): raise ValueError('Invalid carrier frequency.')
        frequency=int(fields['frequency'])
        if not 10000<=frequency<=1000000: raise ValueError('Carrier frequency must be 10,000–1,000,000 Hz.')
        try: duty=Decimal(fields['duty_cycle'])
        except (InvalidOperation,TypeError,ValueError): raise ValueError('Invalid duty cycle.')
        if not duty.is_finite() or not 0<duty<=1: raise ValueError('Duty cycle must be greater than zero and at most one.')
        if for_cli and duty*100 != (duty*100).to_integral_value():
            raise ValueError('CLI duty cycle requires exact one-percent steps.')
        data=fields['data']
        if not isinstance(data,str) or not re.fullmatch(r'\d+(?:\s+\d+)*',data): raise ValueError('Raw timings must be positive integers.')
        values=data.split()
        if not 1<=len(values)<=(512 if for_cli else 1024) or any(len(x)>(7 if for_cli else 10) for x in values): raise ValueError('Raw signal exceeds timing limits.')
        timings=[int(x) for x in values]
        if any(not 1<=x<=(1000000 if for_cli else 4294967295) for x in timings) or (for_cli and sum(timings)>2000000):
            raise ValueError('Raw timings must be positive and total at most two seconds.')
        command='ir tx RAW F:' + str(frequency) + ' DC:' + str(int(duty*100)) + ' ' + ' '.join(map(str,timings))
    else:
        raise ValueError('Unsupported IR signal type.')
    if for_cli and len(command)>960: raise ValueError('Signal exceeds this adapter’s 960-character CLI command limit.')
    return command


def parse_ir_capabilities(body):
    text=body.decode('utf-8',errors='strict')
    found=re.search(r'Available protocols:([^\r\n]*)',text)
    if not found or 'ir tx <protocol> <address> <command>' not in text:
        raise StorageError('IR CLI capability response is unsupported or busy.')
    protocols=sorted(set(found.group(1).split()) & PROTOCOL_BITS.keys())
    raw='ir tx RAW F:' in text
    if not protocols and not raw: raise StorageError('No supported IR transmit formats advertised.')
    return {'protocols':protocols,'raw':raw}


def execute_ir(client, operation, request):
    if operation=='ir_probe':
        client.header('ir')
        return parse_ir_capabilities(client.finish(prompt=PROMPT))
    if operation!='ir_transmit': raise StorageError('Unsupported IR operation.')
    entry=request['entry']; capabilities=request['capabilities']
    command=signal_command(entry)
    kind=entry['fields']['type']
    if (kind=='raw' and capabilities.get('raw') is not True) or (kind=='parsed' and entry['fields']['protocol'] not in capabilities.get('protocols',[])):
        raise StorageError('This signal format was not advertised by the current device.')
    client.header(command)
    body=client.finish(prompt=PROMPT)
    if body.strip():
        raise StorageError('IR command returned an error or unrecognized response: ' + body.decode('utf-8',errors='replace')[:300])
    return {'completed':True}
