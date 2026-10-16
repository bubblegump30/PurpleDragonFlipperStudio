"""Launch the actual packaged GUI with temporary settings, render a PNG and exit."""
import argparse
from pathlib import Path
import struct
import subprocess
import tempfile


def smoke(executable):
    executable=executable.resolve()
    with tempfile.TemporaryDirectory(prefix='purple-dragon-smoke-') as directory:
        root=Path(directory);image=root/'startup.png'
        subprocess.run([str(executable),'--isolated-settings',str(root/'settings.ini'),'--screenshot',str(image),'--size','1280x850'],check=True,timeout=45)
        data=image.read_bytes()
        if data[:8]!=b'\x89PNG\r\n\x1a\n' or len(data)<24:raise RuntimeError('Packaged application did not render a PNG.')
        width,height=struct.unpack('>II',data[16:24])
        if width<980 or height<760:raise RuntimeError('Packaged application rendered an unexpected size.')
        print('Packaged GUI launched, rendered and exited successfully with isolated settings.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('executable',type=Path)
    smoke(parser.parse_args().executable)
