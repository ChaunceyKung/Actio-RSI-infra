"""Trusted installed entry points are the extension boundary, never config imports."""
from importlib.metadata import entry_points
from hashlib import sha256
from pathlib import Path
from actio.contracts.json import ContractError


def resolve(name):
    entries = [ep for ep in entry_points(group='actio.environments') if ep.name == name]
    if len(entries) != 1:
        raise ContractError('unknown or ambiguous installed environment: ' + name)
    entry = entries[0]
    factory = entry.load()
    identity = {'name': name, 'entry_point': entry.value,
                'distribution': entry.dist.name, 'version': entry.dist.version}
    # A local rebuild may retain its package version. Bind installed executable
    # source bytes as well, so an old request key cannot silently reuse new code.
    source_files = sorted((f for f in entry.dist.files or []
                           if f.suffix in {'.py', '.mjs', '.sql', '.json'}), key=str)
    identity['source_sha256'] = sha256(''.join(
        f'{f}:{sha256(Path(entry.dist.locate_file(f)).read_bytes()).hexdigest()}\n'
        for f in source_files).encode()).hexdigest()
    if hasattr(factory, 'identity'):
        identity['backend'] = factory.identity()
    return factory, identity
