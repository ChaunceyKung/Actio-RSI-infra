"""Install the verified upstream source closure into this interpreter's venv."""
import hashlib
import io
import json
from pathlib import Path
import sys
import urllib.request
import zipfile


def main():
    root = Path(__file__).resolve().parents[1]
    pin = json.loads((root / 'src/actio/resources/pins/concordia.json').read_bytes())
    url = f"https://codeload.github.com/google-deepmind/concordia/zip/{pin['sha']}"
    with urllib.request.urlopen(url, timeout=45) as response:
        raw = response.read(32 * 1024 * 1024 + 1)
    if hashlib.sha256(raw).hexdigest() != pin['archive_sha256']:
        raise ValueError('Concordia archive hash mismatch')
    site = Path(sys.prefix) / ('Lib/site-packages' if sys.platform == 'win32' else
                               f'lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages')
    prefix = f"concordia-{pin['sha']}/"
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        files = {n.removeprefix(prefix): archive.read(n) for n in archive.namelist()
                 if not n.endswith('/') and (n.removeprefix(prefix) == 'LICENSE' or
                    n.removeprefix(prefix).startswith('concordia/') and n.endswith('.py'))}
    if set(files) != set(pin['files']):
        raise ValueError('Concordia source set mismatch')
    for name, data in files.items():
        if hashlib.sha256(data).hexdigest() != pin['files'][name]:
            raise ValueError('Concordia file hash mismatch: ' + name)
    for name, data in files.items():
        target = site / (name if name != 'LICENSE' else 'actio-concordia.LICENSE')
        if not target.resolve().is_relative_to(site.resolve()):
            raise ValueError('unsafe archive path')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    print(json.dumps({'concordia': pin['sha'], 'files_verified': len(files),
                      'mode': 'unaltered upstream source closure; not full research stack'}))


if __name__ == '__main__':
    main()
