"""
LINZA.Detector — PDF report generator
Approach: build HTML with the Linza CSS design system → convert to PDF via WeasyPrint.

Public API (drop-in replacement for the original generate_pdf):
    generate_pdf(filename, sections, source_info=None, stats=None)

Data contracts are identical to the original:
    - source_info  — object with attributes:
          video_path, video_duration_formatted, analysis_timestamp,
          processing_time_seconds, frameCount
    - sections     — list of dicts, each:
          {
            "title": str,
            "status": bool,          # True = failed
            "status_table": list[StatusRow],   # .parameter .status .founded
            "problems_table": list[ProblemRow] # .category .start_time .end_time .confidence
          }
    - stats        — dict[str, int]  category → count
"""

from __future__ import annotations

import html as _html
import json
from dataclasses import dataclass
from typing import Any, Optional

# ──────────────────────────────────────────────────────────────────────────────
# CSS (embedded — no external file dependency; mirrors report.css tokens)
# ──────────────────────────────────────────────────────────────────────────────

_CSS = """
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700;9..40,800&display=swap');

/* ── Reset ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

/* ── Tokens (light theme used for print) ── */
:root {
  --linza-bg:              #edf0f8;
  --linza-surface:         rgba(255,255,255,0.82);
  --linza-sidebar:         rgba(255,255,255,0.45);
  --linza-border:          rgba(0,0,0,0.07);
  --linza-border-hover:    rgba(0,0,0,0.13);
  --linza-border-accent:   rgba(60,100,200,0.16);

  --linza-text:            #283050;
  --linza-text-secondary:  #5a6494;
  --linza-text-muted:      #8a90b8;
  --linza-text-heading:    #181e38;

  --linza-blue:            #3a6cd0;
  --linza-green:           #10b981;
  --linza-red:             #ef4444;
  --linza-yellow:          #eab308;
  --linza-purple:          #7c3aed;
  --linza-orange:          #ea580c;
  --linza-cyan:            #0891b2;

  --linza-card-shadow:     0 2px 12px rgba(0,0,0,0.06), inset 0 1px 0 rgba(255,255,255,0.8);
  --linza-blur:            0px; /* WeasyPrint: backdrop-filter not supported */

  font-family: 'DM Sans', system-ui, -apple-system, sans-serif;
  color: var(--linza-text);
  -webkit-font-smoothing: antialiased;
}

/* ── Page setup ── */
@page {
  size: A4;
  margin: 14mm 15mm 18mm 15mm;
  @bottom-center {
    content: "Страница " counter(page) " из " counter(pages);
    font-family: 'DM Sans', sans-serif;
    font-size: 9px;
    color: var(--linza-text-muted);
  }
}

body {
  background: var(--linza-bg);
  font-size: 13px;
  line-height: 1.5;
}

/* ── Typography helpers ── */
.heading-xl { font-size: 22px; font-weight: 800; color: var(--linza-text-heading); letter-spacing: -0.03em; }
.heading-lg { font-size: 17px; font-weight: 800; color: var(--linza-text-heading); letter-spacing: -0.02em; }
.heading-md { font-size: 14px; font-weight: 700; color: var(--linza-text-heading); }
.heading-sm { font-size: 12px; font-weight: 700; color: var(--linza-text); }
.label      { font-size: 10px; font-weight: 600; color: var(--linza-text-secondary); text-transform: uppercase; letter-spacing: 0.06em; }
.mono       { font-family: 'JetBrains Mono','SF Mono',monospace; font-variant-numeric: tabular-nums; }

/* ── Card / glass ── */
.card {
  background: var(--linza-surface);
  border: 1px solid var(--linza-border);
  border-radius: 14px;
  padding: 18px 20px;
  box-shadow: var(--linza-card-shadow);
  position: relative;
  overflow: hidden;
  break-inside: avoid;
}
.card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.9), transparent);
}

/* ── Header ── */
.report-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--linza-border);
}
.logo-block { display: flex; flex-direction: column; gap: 3px; }
.logo-name {
  font-size: 22px;
  font-weight: 800;
  color: var(--linza-blue);
  letter-spacing: -0.04em;
}
.logo-sub { font-size: 11px; color: var(--linza-text-secondary); font-weight: 500; }
.result-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 100px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.03em;
}
.result-pill--pass {
  background: rgba(16,185,129,0.10);
  border: 1px solid rgba(16,185,129,0.22);
  color: var(--linza-green);
}
.result-pill--fail {
  background: rgba(239,68,68,0.08);
  border: 1px solid rgba(239,68,68,0.18);
  color: var(--linza-red);
}
.result-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  display: inline-block;
}
.result-pill--pass .result-dot { background: var(--linza-green); }
.result-pill--fail .result-dot { background: var(--linza-red); }

/* ── Meta grid ── */
.meta-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 20px;
}
.meta-item {
  background: var(--linza-surface);
  border: 1px solid var(--linza-border);
  border-radius: 10px;
  padding: 12px 14px;
}
.meta-item__label { font-size: 10px; font-weight: 600; color: var(--linza-text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
.meta-item__value { font-size: 13px; font-weight: 600; color: var(--linza-text-heading); word-break: break-all; }

/* ── Stats chart (SVG bar chart) ── */
.chart-wrap {
  margin-bottom: 20px;
  break-after: page;
}
.chart-title {
  font-size: 12px;
  font-weight: 700;
  color: var(--linza-text-heading);
  margin-bottom: 12px;
}

/* ── Section ── */
.section { margin-bottom: 24px; break-inside: avoid; }
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

/* ── Badge ── */
.badge {
  display: inline-flex; align-items: center; gap: 3px;
  padding: 3px 9px; border-radius: 16px;
  font-size: 10px; font-weight: 600; white-space: nowrap;
  border: 1px solid transparent;
}
.badge--green { background: rgba(16,185,129,0.08); border-color: rgba(16,185,129,0.18); color: var(--linza-green); }
.badge--red   { background: rgba(239,68,68,0.07);  border-color: rgba(239,68,68,0.15);  color: var(--linza-red); }

/* ── Tables ── */
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
}
th {
  background: rgba(0,0,0,0.03);
  color: var(--linza-text-secondary);
  font-size: 10px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.05em;
  padding: 7px 10px;
  text-align: left;
  border-bottom: 1px solid var(--linza-border);
}
td {
  padding: 7px 10px;
  border-bottom: 1px solid var(--linza-border);
  color: var(--linza-text);
  vertical-align: top;
}
tr:last-child td { border-bottom: none; }

.row-pass td { background: rgba(16,185,129,0.05); }
.row-fail td { background: rgba(239,68,68,0.04); }

.td-status-pass { color: var(--linza-green); font-weight: 600; }
.td-status-fail { color: var(--linza-red);   font-weight: 600; }

.confidence-bar-wrap { display: flex; align-items: center; gap: 6px; }
.confidence-bar-track {
  flex: 1; height: 5px; background: rgba(0,0,0,0.06);
  border-radius: 4px; overflow: hidden;
}
.confidence-bar-fill { height: 100%; border-radius: 4px; background: var(--linza-red); }
.confidence-val { font-size: 10px; font-weight: 600; color: var(--linza-text-secondary); min-width: 36px; }

/* col widths */
.col-num   { width: 28px; }
.col-param { width: 46%; }
.col-stat  { width: 18%; }
.col-found { width: 28%; }

.col-cat   { width: 40%; }
.col-time  { width: 16%; }
.col-conf  { width: 26%; }

/* ── Spacers ── */
.spacer-sm { height: 8px; }
.spacer-md { height: 16px; }
"""

# ──────────────────────────────────────────────────────────────────────────────
# SVG bar chart (pure SVG — no matplotlib, no external deps)
# ──────────────────────────────────────────────────────────────────────────────

def _build_svg_chart(stats: dict[str, int]) -> str:
    if not stats:
        return ""

    categories = list(stats.keys())
    values = list(stats.values())
    max_val = max(values) if values else 1

    # layout
    W, H = 740, 260
    pad_l, pad_r, pad_t, pad_b = 42, 20, 30, 80
    chart_w = W - pad_l - pad_r
    chart_h = H - pad_t - pad_b
    n = len(categories)
    bar_gap = 8
    bar_w = max(10, (chart_w - bar_gap * (n + 1)) // n)

    # y-grid lines (5 levels)
    grid_lines = 5
    svg_parts = [
        f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%;height:auto;font-family:\'DM Sans\',sans-serif;">'
    ]

    # grid
    for i in range(grid_lines + 1):
        y = pad_t + chart_h - i * chart_h // grid_lines
        gv = round(max_val * i / grid_lines)
        svg_parts.append(
            f'<line x1="{pad_l}" y1="{y}" x2="{W - pad_r}" y2="{y}" '
            f'stroke="#e2e5ef" stroke-width="1"/>'
            f'<text x="{pad_l - 5}" y="{y + 4}" text-anchor="end" '
            f'font-size="9" fill="#8a90b8">{gv}</text>'
        )

    # bars
    bar_color_base = "#3a6cd0"
    bar_color_alpha = 0.75
    for i, (cat, val) in enumerate(zip(categories, values)):
        x = pad_l + bar_gap + i * (bar_w + bar_gap)
        bar_h_px = int(val / max_val * chart_h) if max_val else 0
        y = pad_t + chart_h - bar_h_px

        # bar body
        svg_parts.append(
            f'<rect x="{x}" y="{y}" width="{bar_w}" height="{bar_h_px}" '
            f'rx="4" fill="{bar_color_base}" opacity="{bar_color_alpha}"/>'
        )

        # value label above bar
        svg_parts.append(
            f'<text x="{x + bar_w // 2}" y="{y - 5}" text-anchor="middle" '
            f'font-size="9" font-weight="700" fill="#283050">{val}</text>'
        )

        # category label (rotated)
        label = _html.escape(cat[:28] + ("…" if len(cat) > 28 else ""))
        lx = x + bar_w // 2
        ly = pad_t + chart_h + 10
        svg_parts.append(
            f'<text transform="rotate(35,{lx},{ly})" x="{lx}" y="{ly}" '
            f'text-anchor="start" font-size="9" fill="#5a6494">{label}</text>'
        )

    # axis lines
    svg_parts.append(
        f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{pad_t + chart_h}" '
        f'stroke="#cdd0de" stroke-width="1.5"/>'
        f'<line x1="{pad_l}" y1="{pad_t + chart_h}" x2="{W - pad_r}" y2="{pad_t + chart_h}" '
        f'stroke="#cdd0de" stroke-width="1.5"/>'
    )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


# ──────────────────────────────────────────────────────────────────────────────
# HTML builder
# ──────────────────────────────────────────────────────────────────────────────

def _e(s: Any) -> str:
    """HTML-escape to string."""
    return _html.escape(str(s) if s is not None else "")


def _build_status_table(rows) -> str:
    rows_html = []
    for i, row in enumerate(rows, 1):
        failed = getattr(row, "status", "") == "Провалено"
        cls = "row-fail" if failed else "row-pass"
        status_cls = "td-status-fail" if failed else "td-status-pass"
        rows_html.append(
            f'<tr class="{cls}">'
            f'<td class="col-num mono">{i}</td>'
            f'<td class="col-param">{_e(row.parameter)}</td>'
            f'<td class="col-stat {status_cls}">{_e(row.status)}</td>'
            f'<td class="col-found">{_e(row.founded)}</td>'
            f'</tr>'
        )
    return (
        '<div class="card" style="padding:0;overflow:hidden;">'
        '<table>'
        '<thead><tr>'
        '<th class="col-num">№</th>'
        '<th class="col-param">Параметр</th>'
        '<th class="col-stat">Статус</th>'
        '<th class="col-found">Обнаружено</th>'
        '</tr></thead>'
        '<tbody>' + "".join(rows_html) + '</tbody>'
        '</table></div>'
    )


def _build_problems_table(rows) -> str:
    if not rows:
        return '<p style="font-size:11px;color:var(--linza-text-muted);padding:6px 0;">Нарушений не обнаружено</p>'

    rows_html = []
    for row in rows:
        conf = float(getattr(row, "confidence", 0))
        bar_pct = int(conf * 100)
        bar_html = (
            f'<div class="confidence-bar-wrap">'
            f'<div class="confidence-bar-track">'
            f'<div class="confidence-bar-fill" style="width:{bar_pct}%"></div>'
            f'</div>'
            f'<span class="confidence-val">{conf:.3f}</span>'
            f'</div>'
        )
        rows_html.append(
            f'<tr class="row-fail">'
            f'<td class="col-cat">{_e(row.category)}</td>'
            f'<td class="col-time mono">{_e(row.start_time)}</td>'
            f'<td class="col-time mono">{_e(row.end_time)}</td>'
            f'<td class="col-conf">{bar_html}</td>'
            f'</tr>'
        )
    return (
        '<div class="card" style="padding:0;overflow:hidden;">'
        '<table>'
        '<thead><tr>'
        '<th class="col-cat">Категория</th>'
        '<th class="col-time">Начало</th>'
        '<th class="col-time">Конец</th>'
        '<th class="col-conf">Уверенность</th>'
        '</tr></thead>'
        '<tbody>' + "".join(rows_html) + '</tbody>'
        '</table></div>'
    )


def _build_html(sections, source_info, stats) -> str:
    # ── Global result
    global_failed = any(s["status"] for s in sections)
    result_cls = "result-pill--fail" if global_failed else "result-pill--pass"
    result_label = "ПРОВАЛЕНО" if global_failed else "УСПЕШНО"

    # ── Meta cards
    si = source_info
    meta_items = [
        ("Источник", getattr(si, "video_path", "—")),
        ("Длительность", getattr(si, "video_duration_formatted", "—")),
        ("Дата анализа", getattr(si, "analysis_timestamp", "—")),
        ("Время обработки", f'{getattr(si, "processing_time_seconds", "—")} сек.'),
        ("Всего сцен", getattr(si, "frameCount", "—")),
        ("Итог", result_label),
    ]
    meta_html = "".join(
        f'<div class="meta-item">'
        f'<div class="meta-item__label">{_e(k)}</div>'
        f'<div class="meta-item__value">{_e(v)}</div>'
        f'</div>'
        for k, v in meta_items
    )

    # ── Chart
    chart_html = ""
    if stats:
        svg = _build_svg_chart(stats)
        chart_html = (
            '<div class="card chart-wrap">'
            '<div class="chart-title">Статистика обнаруженных нарушений по категориям</div>'
            + svg +
            '</div>'
        )

    # ── Sections
    sections_html_parts = []
    for sec in sections:
        failed = sec["status"]
        badge_cls = "badge--red" if failed else "badge--green"
        badge_label = "Провалено" if failed else "Успешно"

        sections_html_parts.append(
            f'<div class="section">'
            f'<div class="section-header">'
            f'<span class="heading-md">{_e(sec["title"])}</span>'
            f'<span class="badge {badge_cls}">{badge_label}</span>'
            f'</div>'
            + _build_status_table(sec.get("status_table", []))
            + '<div class="spacer-sm"></div>'
            + '<div class="heading-sm" style="margin-bottom:6px;">Обнаруженные проблемы</div>'
            + _build_problems_table(sec.get("problems_table", []))
            + '</div>'
        )

    sections_html = "".join(sections_html_parts)

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>LINZA.Detector — Отчет</title>
<style>{_CSS}</style>
</head>
<body>
  <!-- HEADER -->
  <div class="report-header">
    <div class="logo-block">
      <span class="logo-name">LINZA.Detector</span>
      <span class="logo-sub">Структурированный отчет по видеофайлу</span>
    </div>
    <span class="result-pill {result_cls}">
      <span class="result-dot"></span>
      {result_label}
    </span>
  </div>

  <!-- META -->
  <div class="meta-grid">{meta_html}</div>

  <!-- CHART -->
  {chart_html}

  <!-- SECTIONS -->
  {sections_html}
</body>
</html>"""


# ──────────────────────────────────────────────────────────────────────────────
# Public entry point
# ──────────────────────────────────────────────────────────────────────────────

def generate_pdf(
    filename: str,
    sections: list,
    source_info=None,
    stats: Optional[dict] = None,
) -> None:
    """Generate a PDF report to *filename* using WeasyPrint."""
    from weasyprint import HTML, CSS

    html_content = _build_html(sections, source_info, stats)

    # Optional: save HTML for debugging
    with open(filename.replace('.pdf', '.html'), 'w', encoding='utf-8') as f:
        f.write(html_content)

    HTML(string=html_content).write_pdf(filename)
    print(f"[generate_pdf] Saved → {filename}")


# ──────────────────────────────────────────────────────────────────────────────
# Demo / smoke test
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from dataclasses import dataclass

    @dataclass
    class SourceInfo:
        video_path: str = "/data/videos/sample_patrol.mp4"
        video_duration_formatted: str = "00:12:47"
        analysis_timestamp: str = "2025-04-09 14:32:05"
        processing_time_seconds: float = 38.4
        frameCount: int = 23041

    @dataclass
    class StatusRow:
        parameter: str
        status: str
        founded: str

    @dataclass
    class ProblemRow:
        category: str
        start_time: str
        end_time: str
        confidence: float

    demo_sections = [
        {
            "title": "Раздел 1: Средства индивидуальной защиты",
            "status": True,
            "status_table": [
                StatusRow("Наличие защитной каски", "Провалено", "3 нарушения"),
                StatusRow("Наличие светоотражающего жилета", "Успешно", "—"),
                StatusRow("Наличие защитных очков", "Провалено", "1 нарушение"),
                StatusRow("Использование защитных перчаток", "Успешно", "—"),
            ],
            "problems_table": [
                ProblemRow("Отсутствие каски", "00:02:14", "00:02:19", 0.921),
                ProblemRow("Отсутствие каски", "00:07:53", "00:07:58", 0.884),
                ProblemRow("Отсутствие каски", "00:11:30", "00:11:36", 0.903),
                ProblemRow("Отсутствие защитных очков", "00:09:10", "00:09:15", 0.762),
            ],
        },
        {
            "title": "Раздел 2: Рабочая зона и ограждения",
            "status": False,
            "status_table": [
                StatusRow("Наличие ограждения опасной зоны", "Успешно", "—"),
                StatusRow("Корректное расположение знаков безопасности", "Успешно", "—"),
            ],
            "problems_table": [],
        },
    ]

    demo_stats = {
        "Отсутствие каски": 3,
        "Отсутствие жилета": 1,
        "Нарушение ограждения": 2,
        "Отсутствие очков": 1,
        "Использование телефона": 4,
        "Несанкционированный доступ": 2,
    }

    generate_pdf(
        "/mnt/user-data/outputs/linza_report_demo.pdf",
        demo_sections,
        source_info=SourceInfo(),
        stats=demo_stats,
    )