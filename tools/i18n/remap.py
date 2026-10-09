#!/usr/bin/env python3
"""Reasigna las traducciones de una página cuando cambió el orden o el contenido del HTML en inglés.

Uso: python3 tools/i18n/remap.py <clave> [<ref-git>]
  1. Lee el src/<clave>.json y el <clave>.txt de <ref-git> (por defecto HEAD): textos en inglés y su traducción.
  2. Lee el src/<clave>.json nuevo (después de correr extract.py).
  3. Alinea ambas listas por texto en inglés (difflib) y reescribe <clave>.txt con las posiciones nuevas.
Los textos nuevos quedan sin traducción: build.py los lista y se agregan a mano.
"""
import json, subprocess, sys, difflib, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
key = sys.argv[1]; ref = sys.argv[2] if len(sys.argv) > 2 else 'HEAD'
rel = f'tools/i18n/es-co/{key}.txt'
git = lambda p: subprocess.run(['git', 'show', f'{ref}:{p}'], cwd=ROOT, capture_output=True, text=True, check=True).stdout
old_src = json.loads(git(f'tools/i18n/es-co/src/{key}.json'))
old_txt = {}
for line in git(rel).splitlines():
    if not line.strip() or line.startswith('#'): continue
    i, _, es = line.partition('|'); a, _, b = i.partition('-')
    for n in range(int(a), int(b or a) + 1): old_txt[n] = es.strip()
new_src = json.loads((ROOT / f'tools/i18n/es-co/src/{key}.json').read_text())
o = [x['en'].strip() for x in old_src]; n = [x['en'].strip() for x in new_src]
sm = difflib.SequenceMatcher(None, o, n, autojunk=False)
out, new_items = {}, []
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == 'equal':
        for k in range(i2 - i1):
            oi = old_src[i1 + k]['i']
            if oi in old_txt: out[new_src[j1 + k]['i']] = old_txt[oi]
    elif tag in ('replace', 'insert'):
        new_items += [(new_src[j]['i'], n[j]) for j in range(j1, j2)]
# bloques movidos: el texto existe en la lista vieja pero difflib no lo alineó; se busca por texto exacto
used = {old_src[k]['i'] for k in range(len(old_src))
        if old_src[k]['i'] in old_txt and old_txt[old_src[k]['i']] in out.values() and False}
by_text = {}
for x in old_src:
    if x['i'] in old_txt: by_text.setdefault(x['en'].strip(), []).append(old_txt[x['i']])
still = []
for i, t in new_items:
    if by_text.get(t):
        out[i] = by_text[t].pop(0)
    else:
        still.append((i, t))
new_items = still
lines = [f'{i}|{out[i]}' for i in sorted(out)]
(ROOT / rel).write_text('\n'.join(lines) + '\n')
print(f'{len(out)} traducciones conservadas; {len(new_items)} textos nuevos sin traducir:')
for i, t in new_items: print(f'  {i}: {t[:110]}')
