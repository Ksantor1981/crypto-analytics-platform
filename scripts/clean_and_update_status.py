import re
from pathlib import Path
from collections import defaultdict, OrderedDict

INPUT_ANN = 'TASKS2_ARCHIVE_DETAILED_STATUS_ANNOTATED.md'
INPUT_PLAIN = 'TASKS2_ARCHIVE_DETAILED_STATUS.md'
OUTPUT = 'TASKS2_ARCHIVE_DEDUPED_STATUS.md'

# Normalize a task text for dedupe (strip bold numbers, extra spaces)
BOLD_NUM_RE = re.compile(r'^\*\*[^*]+\*\*\s*')
CB_ANN_RE = re.compile(r'^-\s*(✅|⬜)\s*\[(IMPL|PARTIAL|TBD)\]\s*(.*)$')
CB_PLAIN_RE = re.compile(r'^-\s*(✅|⬜)\s*(.*)$')
H1_RE = re.compile(r'^##\s+(.+)$')
H2_RE = re.compile(r'^###\s+(.+)$')
H3_RE = re.compile(r'^####\s+(.+)$')

# Status precedence for merging duplicates: IMPL > PARTIAL > TBD
TAG_ORDER = { 'IMPL': 3, 'PARTIAL': 2, 'TBD': 1 }
MARK_ORDER = { '✅': 2, '⬜': 1 }

# Explicit overrides for specific tasks
OVERRIDES = {
    # Frontend critical 1.6.x
    'исправить ошибку подключения next.js приложения': ('✅', 'IMPL'),
    'настроить корректные environment variables для frontend': ('⬜', 'PARTIAL'),
    'исправить docker конфигурацию для frontend': ('⬜', 'PARTIAL'),
    'добавить health checks для frontend': ('⬜', 'TBD'),
    'создать fallback страницу при недоступности': ('⬜', 'TBD'),
}

def normalize_text(s: str) -> str:
    s = s.strip()
    s = BOLD_NUM_RE.sub('', s)
    s = re.sub(r'\s+', ' ', s)
    return s.lower()


def apply_overrides(text_norm: str, mark: str, tag: str) -> tuple[str, str]:
    for key, (m, t) in OVERRIDES.items():
        if key in text_norm:
            return m, t
    return mark, tag


def main() -> int:
    root = Path.cwd()
    src_path = root / INPUT_ANN
    src_type = 'ANN'
    if not src_path.exists():
        src_path = root / INPUT_PLAIN
        src_type = 'PLAIN'
        if not src_path.exists():
            print('No input files found', flush=True)
            return 1

    lines = src_path.read_text(encoding='utf-8').splitlines()

    h1 = h2 = h3 = None
    groups: dict[tuple[str,str,str], OrderedDict[str, dict]] = defaultdict(OrderedDict)

    for line in lines:
        m1 = H1_RE.match(line)
        if m1:
            h1 = m1.group(1).strip()
            h2 = h3 = None
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

        mark = tag = None
        text = None
        if src_type == 'ANN':
            m = CB_ANN_RE.match(line)
            if not m:
                continue
            mark, tag, text = m.groups()
        else:
            m = CB_PLAIN_RE.match(line)
            if not m:
                continue
            mark, text = m.groups()
            tag = 'TBD'

        text_norm = normalize_text(text)
        mark, tag = apply_overrides(text_norm, mark, tag)

        key = (h1 or '', h2 or '', h3 or '')
        bucket = groups[key]
        if text_norm not in bucket:
            bucket[text_norm] = { 'mark': mark, 'tag': tag, 'text': text }
        else:
            # Merge: keep strongest tag/mark
            cur = bucket[text_norm]
            if TAG_ORDER.get(tag, 0) > TAG_ORDER.get(cur['tag'], 0):
                cur['tag'] = tag
            if MARK_ORDER.get(mark, 0) > MARK_ORDER.get(cur['mark'], 0):
                cur['mark'] = mark

    # Write output
    out = []
    out.append('# Дедуплицированная сводка статусов (аннотированная)')
    out.append('')
    out.append('Легенда: ✅ выполнено; ⬜ не выполнено. Теги: [IMPL] реализовано, [PARTIAL] частично, [TBD] требуется сделать/подтвердить.')
    out.append('')

    for key in sorted(groups.keys()):
        gh1, gh2, gh3 = key
        if gh1:
            out.append(f'## {gh1}')
        if gh2:
            out.append(f'### {gh2}')
        if gh3:
            out.append(f'#### {gh3}')
        for item in groups[key].values():
            out.append(f"- {item['mark']} [{item['tag']}] {item['text']}")
        out.append('')

    (root / OUTPUT).write_text('\n'.join(out), encoding='utf-8')
    print(f'Wrote {OUTPUT}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
