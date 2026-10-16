"""Conservative digital GPIO CLI adapter; no debug, power, ADC or PWM pins."""
import re
from .sd_protocol import StorageError

PINS={'PA7':2,'PA6':3,'PA4':4,'PB3':5,'PB2':6,'PC3':7,'PC1':15,'PC0':16}
PROMPT=re.compile(rb'(?:^|\r\n)>: $')


def execute_gpio(client, operation, request):
    state=client.gpio_state
    if operation=='gpio_probe':
        state.clear()
        client.header('gpio'); body=client.finish(prompt=PROMPT).decode('utf-8',errors='strict')
        if not all(x in body for x in ('gpio <cmd> <args>','mode <pin_name> <0|1>','set <pin_name> <0|1>','read <pin_name>','0 - input, 1 - output')):
            raise StorageError('Unsupported GPIO CLI usage; no GPIO actions enabled.')
        state.update(supported=True,modes={})
        return {'supported':True}
    if operation!='gpio_action' or not isinstance(request,dict):raise StorageError('Invalid GPIO request.')
    pin=request.get('pin'); action=request.get('action')
    if pin not in PINS or action not in ('Input','Output','Read','LOW','HIGH'):raise StorageError('Unsupported GPIO pin or action.')
    if not state.get('supported'):raise StorageError('Check GPIO support in this session first.')
    mode=state['modes'].get(pin)
    if action=='Read' and mode!='Input':raise StorageError('Set Input before Read.')
    if action in ('LOW','HIGH') and mode!='Output':raise StorageError('Set Output before writing.')
    suffix={'Input':'mode '+pin+' 0','Output':'mode '+pin+' 1','Read':'read '+pin,'LOW':'set '+pin+' 0','HIGH':'set '+pin+' 1'}[action]
    client.header('gpio '+suffix); body=client.finish(prompt=PROMPT).decode('utf-8',errors='strict').strip()
    expected={'Input':'Pin '+pin+' is now an input','Output':'Pin '+pin+' is now an output (low)','LOW':'Pin '+pin+' => 0','HIGH':'Pin '+pin+' => 1'}
    value=None
    if action=='Read':
        match=re.fullmatch('Pin '+pin+r' <= ([01])',body)
        if match:value=int(match.group(1))
        else:raise StorageError('Unrecognized GPIO read response: '+body[:200])
    elif body!=expected[action]:raise StorageError('GPIO command did not confirm the requested action: '+body[:200])
    if action in ('Input','Output'):state['modes'][pin]=action
    if action in ('Output','LOW'):value=0
    if action=='HIGH':value=1
    return {'pin':pin,'action':action,'value':value,'response':body}
