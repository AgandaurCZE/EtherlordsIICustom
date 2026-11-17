#!/usr/bin/env python3
"""Offline Etherlords II Lua 4-compatible concatenation builder."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent
FILES = [ROOT / 'src/encounters/bee_queen.lua', ROOT / 'src/shared/hook_router.lua']
OUTPUT = ROOT / 'build/TestMap.scp'


def main():
    contents = []
    hook_names = {}
    func_names = {}
    for path in FILES:
        source = path.read_text(encoding='utf-8')
        for name in re.findall(r'^function\s+([A-Za-z_][A-Za-z_0-9]*)\s*\(', source, re.M):
            if name in func_names:
                sys.exit(f'ERROR: duplicate global function {name} in {path} and {func_names[name]}')
            func_names[name] = path
            if name.startswith('Hook_'):
                hook_names[name] = path
        if re.search(r'\b(?:goto|continue|require|dofile|loadfile)\s*\(', source):
            sys.exit(f'ERROR: unsupported/uncertified runtime loading in {path}')
        if re.search(r'\blocal\b', re.sub(r'--[^\n]*', '', source)):
            sys.exit(f'ERROR: local declarations disallowed for these modules (Lua 4 outer-scope capture hazard): {path}')
        contents.append(f'-- ===== BEGIN {path.relative_to(ROOT)} =====\n{source.rstrip()}\n-- ===== END =====')
    expected = {'Hook_OnStep','Hook_OnCloseMessageBox','Hook_OnBattleFinishing','Hook_OnPreUse'}
    if set(hook_names) != expected:
        sys.exit('ERROR: unexpected engine hooks: ' + repr(sorted(hook_names)))
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text('-- GENERATED FILE; edit src/ only.\n-- Etherlords II Lua 4.0.\n\n' + '\n\n'.join(contents) + '\n', encoding='utf-8')
    print(f'Wrote {OUTPUT} ({OUTPUT.stat().st_size} bytes)')
    print(f'Validated {len(func_names)} unique named functions, {len(hook_names)} engine hooks.')

if __name__ == '__main__':
    main()
