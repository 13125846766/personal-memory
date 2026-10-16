#!/usr/bin/env python3
"""Install/upgrade the standalone skill without reading or copying a private vault."""
import argparse
from pathlib import Path
import shutil


def install(target, upgrade=False):
    source = Path(__file__).resolve().parent / 'skills' / 'personal-memory'
    target = Path(target).expanduser().resolve()
    if target == source or source in target.parents or target in source.parents:
        raise ValueError('Installation target must be separate from the source package.')
    if target.exists() and not upgrade:
        raise ValueError('Skill already exists. Review the target, then use --upgrade to replace package files.')
    if target.exists():
        for item in target.rglob('*'):
            if item.is_symlink():
                raise ValueError('Installation target contains symlinks; review them before upgrading.')
    target.mkdir(parents=True, exist_ok=True)
    count = 0
    for path in source.rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
            relative = path.relative_to(source)
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
            count += 1
    return target, count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', type=Path, default=Path.home() / '.agents' / 'skills' / 'personal-memory')
    parser.add_argument('--upgrade', action='store_true')
    args = parser.parse_args()
    try:
        target, count = install(args.target, args.upgrade)
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Install failed: {exc}\n')
    print(f'Installed {count} files: {target}')
    print('Private data was not read or copied. Reopen your skill list if necessary.')
    print(f'Local UI: python "{target / "scripts" / "memory.py"}" serve --open')


if __name__ == '__main__':
    main()
