import os
import re
import sys
from pathlib import Path

ARCHIVE_FILE = 'TASKS2-архив.log'
OUTPUT_FILE = 'TASKS2_ARCHIVE_DETAILED_STATUS.md'

# Fallback encodings to try if utf-8 fails
CANDIDATE_ENCODINGS = ['utf-8', 'utf-8-sig', 'cp1251', 'latin-1']

CHECKBOX_RE = re.compile(r'^\s*- \[( |x)\]\s*(.*)$')
H1_RE = re.compile(r'^#\s+(.+)$')
H2_RE = re.compile(r'^##\s+(.+)$')
H3_RE = re.compile(r'^###\s+(.+)$')


def read_text_with_fallback(path: Path) -> str:
    for enc in CANDIDATE_ENCODINGS:
        try:
            return path.read_text(encoding=enc)
        except Exception:
            continue
    # As last resort, read bytes and decode replacing errors
    return path.read_bytes().decode('utf-8', errors='replace')


def main() -> int:
    root = Path.cwd()
    archive_path = root / ARCHIVE_FILE
    if not archive_path.exists():
        print(f'Archive file not found: {archive_path}', file=sys.stderr)
        return 1

    content = read_text_with_fallback(archive_path)

    # State trackers for current headers
    h1 = None
    h2 = None
    h3 = None

    # Collected items: list of dicts
    items = []

    for raw_line in content.splitlines():
        line = raw_line.rstrip('\n')
        m1 = H1_RE.match(line)
        if m1:
            h1 = m1.group(1).strip()
            h2 = None
            h3 = None
            continue
        m2 = H2_RE.match(line)
        if m2:
            h2 = m2.group(1).strip()
            h3 = None
            continue
        m3 = H3_RE.match(line)
        if m3:
            h3 = m3.group(1).strip()
            continue

        cb = CHECKBOX_RE.match(line)
        if cb:
            done = (cb.group(1) == 'x')
            text = cb.group(2).strip()
            items.append({
                'h1': h1,
                'h2': h2,
                'h3': h3,
                'done': done,
                'text': text,
            })

    # Group by (h1, h2, h3)
    from collections import defaultdict
    groups = defaultdict(list)
    for it in items:
        key = (it['h1'] or '', it['h2'] or '', it['h3'] or '')
        groups[key].append(it)

    # Write markdown
    out = []
    out.append('# Подробная сводка статусов из TASKS2-архив')
    out.append('')
    out.append('Легенда: ✅ выполнено, ⬜ не выполнено (по состоянию чекбоксов в архиве).')
    out.append('Файл сгенерирован автоматически из TASKS2-архив.log; оригинал не изменён.')
    out.append('')

    # Sort groups in a readable order
    def _key_order(k):
        return tuple(s or '' for s in k)

    for (gh1, gh2, gh3) in sorted(groups.keys(), key=_key_order):
        if gh1:
            out.append(f'## {gh1}')
        if gh2:
            out.append(f'### {gh2}')
        if gh3:
            out.append(f'#### {gh3}')
        for it in groups[(gh1, gh2, gh3)]:
            mark = '✅' if it['done'] else '⬜'
            out.append(f'- {mark} {it["text"]}')
        out.append('')

    (root / OUTPUT_FILE).write_text('\n'.join(out), encoding='utf-8')
    print(f'Written {OUTPUT_FILE} with {len(items)} items')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
