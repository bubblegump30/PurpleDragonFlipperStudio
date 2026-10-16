"""Read-only compatibility snapshots; never probe or include device identifiers."""
import platform
import sys
import PySide6
import serial
from . import __version__


def compatibility_snapshot(window):
    identified=window.sd_ready()
    capabilities=window.device_adapter.capabilities if identified else frozenset()
    rows=[]
    for name,cap,step in [('Identity','device_info','Identify / Refresh device in CLI mode'),
                          ('SD files & backups','sd_files','SD Files → Refresh / Probe SD'),
                          ('IR transmission','ir_tx','IR Remote Studio → Check IR support'),
                          ('Digital GPIO','gpio_digital','GPIO Lab → Check GPIO support')]:
        rows.append({'area':name,'status':'Checked this session' if cap in capabilities else 'Not checked',
                     'next_step':'Available within adapter limits; physical behavior unverified' if cap in capabilities else step})
    rows.append({'area':'Apps / battery / ADC / PWM','status':'Unavailable','next_step':'Not implemented by these adapters'})
    if not window.connected or window.last_connection_error or window.connection_cancelled or window.connection_lost:recovery='Reconnect the selected USB port, identify in CLI mode, then repeat workspace support checks.'
    elif window.mode.currentText()!='CLI':recovery='Disconnect, choose CLI mode, reconnect and identify for device workspaces.'
    elif not identified:recovery='Identify / Refresh device. A serial connection alone does not establish compatibility.'
    else:recovery='Run each required workspace support check. Support is based on responses, not firmware version guesses.'
    checks=[]
    checks.append({'area':'Settings storage','ok':window.settings.status().name=='NoError'})
    checks.append({'area':'GPIO setup store','ok':window.profile_store_error() is None})
    try:window.ir_library_data();valid=True
    except (ValueError,TypeError):valid=False
    checks.append({'area':'IR library store','ok':valid})
    try:window.favorite_commands();valid=True
    except (ValueError,TypeError):valid=False
    checks.append({'area':'Command favorites','ok':valid})
    return {'schema':1,'application':'PurpleDragonFlipperStudio','version':__version__,
            'runtime':{'python':platform.python_version(),'platform':sys.platform,'pyside6':PySide6.__version__,'pyserial':serial.__version__},
            'connection':{'state':window.connection_state,'mode':window.mode.currentText(),'identity':window.device_adapter.state,'busy':bool(window.sd_busy)},
            'capabilities':rows,'local_checks':checks,'recovery':recovery,
            'contracts':{'identity':'device_info major 2, Flipper Zero target 7','prompt':'unprefixed >: prompt on its own line',
                         'gpio':'eight regular pins; digital only','ir':'advertised parsed/raw formats within adapter limits','storage':'/ext, 4 MiB/file'},
            'limitations':['Protocol compatibility is not cryptographic authentication or physical hardware validation.',
                           'Disconnect does not reset GPIO outputs; interrupted SD writes may leave partial new data.',
                           'No automatic reconnection, replay or hardware commands from this report.']}
