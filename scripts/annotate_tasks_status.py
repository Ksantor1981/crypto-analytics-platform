import re
from pathlib import Path

INPUT = 'TASKS2_ARCHIVE_DETAILED_STATUS.md'
OUTPUT = 'TASKS2_ARCHIVE_DETAILED_STATUS_ANNOTATED.md'

# Heuristic tag rules: (pattern -> tag)
RULES = [
    (re.compile(r'(?i)kubernetes|helm|ingress|hpa|deployment'), 'IMPL'),
    (re.compile(r'(?i)shadcn|tailwind|ui\s*components|tokenmetrics|редизайн|дизайн'), 'IMPL'),
    (re.compile(r'(?i)i18n|мультиязычн|переключатель языка|language'), 'IMPL'),
    (re.compile(r'(?i)stripe|подписк|оплат|webhook'), 'PARTIAL'),
    (re.compile(r'(?i)oauth|google|oidc|social\s+login'), 'PARTIAL'),
    (re.compile(r'(?i)auto[-_ ]?trading|торгов(ый|ля)|risk management|portfolio'), 'PARTIAL'),
    (re.compile(r'(?i)bybit|binance|kucoin|exchange'), 'PARTIAL'),
    (re.compile(r'(?i)prometheus|grafana|monitor(ing)?|dashboard'), 'PARTIAL'),
    (re.compile(r'(?i)ci/cd|github\s+actions|staging'), 'TBD'),
    (re.compile(r'(?i)секрет|secret key|api key|env|secrets?'), 'TBD'),
]

CB_RE = re.compile(r'^-\s*(✅|⬜)\s*(.*)$')


def tag_for(text: str) -> str | None:
    for rx, tag in RULES:
        if rx.search(text):
            return tag
    return None


def main() -> int:
    p = Path(INPUT)
    content = p.read_text(encoding='utf-8')
    out_lines = []
    for line in content.splitlines():
        m = CB_RE.match(line)
        if m:
            mark, text = m.groups()
            tag = tag_for(text) or 'TBD'
            out_lines.append(f'- {mark} [{tag}] {text}')
        else:
            out_lines.append(line)
    Path(OUTPUT).write_text('\n'.join(out_lines), encoding='utf-8')
    print(f'Wrote {OUTPUT}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
