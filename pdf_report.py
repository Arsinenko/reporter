"""
LINZA.Detector — PDF report generator
v3: full-bleed bg, fixed chart clipping (labels + scale), @page margin = body padding
"""

from __future__ import annotations

import html as _html
from typing import Any, Optional

_CSS = """
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700;9..40,800&family=DM+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg:            #edf0f8;
  --surface:       #ffffff;
  --surface-alt:   #f4f5fb;
  --border:        #c8cde0;
  --border-strong: #a0a8c8;
  --text:          #1a2040;
  --text-secondary:#4a5280;
  --text-muted:    #8892b8;
  --accent:        #2555c8;
  --green:         #059669;
  --red:           #dc2626;
  --zebra:         #f2f3f9;
  font-family: 'DM Sans', system-ui, sans-serif;
  color: var(--text);
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}

/* 3 mm margins — content fills the page edge-to-edge with just a sliver of space */
@page {
  size: A4;
  margin: 3mm;
  background: var(--bg);
}

html, body {
  background: var(--bg);
  font-size: 12px;
  line-height: 1.55;
  margin: 0;
  padding: 8px 10px;
  width: 100%;
}

/* ── Typography ── */
.mono       { font-family: 'DM Mono', 'Courier New', monospace; font-size: 11px; }
.heading-md { font-size: 13px; font-weight: 700; color: var(--text); }
.heading-sm { font-size: 11px; font-weight: 700; color: var(--text); }

/* ── Report Header ── */
.report-header {
  display: table;
  width: 100%;
  padding: 14px 18px;
  background: var(--text);
  border-radius: 8px;
  margin-bottom: 10px;
  color: #fff;
}
.report-header__left  { display: table-cell; vertical-align: middle; }
.report-header__right { display: table-cell; vertical-align: middle; text-align: right; width: 150px; }

.logo-name { font-size: 20px; font-weight: 800; color: #fff; letter-spacing: -0.04em; }
.logo-dot  { color: #5b8aff; }
.logo-sub  { font-size: 10px; font-weight: 500; color: rgba(255,255,255,0.42); margin-top: 2px;
             letter-spacing: 0.04em; text-transform: uppercase; }

.result-badge {
  display: inline-block;
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  white-space: nowrap;
}
.result-badge--pass { background: rgba(5,150,105,0.18); border: 1.5px solid rgba(5,150,105,0.45); color: #34d399; }
.result-badge--fail { background: rgba(220,38,38,0.18);  border: 1.5px solid rgba(220,38,38,0.45);  color: #f87171; }

/* ── Meta grid — real HTML table, no flexbox ── */
.meta-table    { width: 100%; border-collapse: separate; border-spacing: 6px; margin-bottom: 10px; }
.meta-item     { background: var(--surface); border: 1px solid var(--border);
                 border-radius: 7px; padding: 9px 11px; vertical-align: top; width: 33.3%; }
.meta-item__label { font-size: 9px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;
                    color: var(--text-muted); margin-bottom: 2px; }
.meta-item__value { font-size: 12px; font-weight: 600; color: var(--text); word-break: break-all; }

/* ── Section ── */
.section { margin-bottom: 16px; }

.section-header {
  display: table;
  width: 100%;
  padding: 9px 13px;
  background: var(--text);
  border-radius: 7px 7px 0 0;
  break-after: avoid;
}
.section-header__left  { display: table-cell; vertical-align: middle; }
.section-header__right { display: table-cell; vertical-align: middle; text-align: right; width: 90px; }
.section-header .heading-md { color: #fff; }

.badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 4px;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.badge--green { background: rgba(5,150,105,0.18); border: 1px solid rgba(5,150,105,0.35); color: #34d399; }
.badge--red   { background: rgba(220,38,38,0.18);  border: 1px solid rgba(220,38,38,0.35);  color: #f87171; }

/* ── Cards ── */
.card            { background: var(--surface); border: 1px solid var(--border);
                   border-radius: 7px; overflow: hidden; margin-bottom: 8px; }
.card--top-flush { border-radius: 0 0 7px 7px; border-top: none; }
.card-inner      { padding: 10px 12px; }

/* ── Tables ── */
table.data-table { width: 100%; border-collapse: collapse; font-size: 11px; }
table.data-table thead th {
  background: var(--surface-alt);
  color: var(--text-muted);
  font-size: 9px; font-weight: 700;
  letter-spacing: 0.08em; text-transform: uppercase;
  padding: 7px 11px; text-align: left;
  border-bottom: 2px solid var(--border-strong);
  border-right: 1px solid var(--border);
}
table.data-table thead th:last-child { border-right: none; }
table.data-table tbody td {
  padding: 6px 11px;
  border-bottom: 1px solid var(--border);
  border-right: 1px solid var(--border);
  vertical-align: middle;
  color: var(--text);
}
table.data-table tbody td:last-child   { border-right: none; }
table.data-table tbody tr:last-child td { border-bottom: none; }
table.data-table tbody tr:nth-child(even) td { background: var(--zebra); }

.status-pass { color: var(--green); font-weight: 700; font-size: 10px;
               letter-spacing: 0.05em; text-transform: uppercase; }
.status-fail { color: var(--red);   font-weight: 700; font-size: 10px;
               letter-spacing: 0.05em; text-transform: uppercase; }
.row-num     { color: var(--text-muted); font-size: 10px;
               font-family: 'DM Mono', monospace; text-align: center; width: 32px; }

/* ── Confidence bar ── */
.conf-wrap       { display: table; width: 100%; table-layout: fixed; }
.conf-track-cell { display: table-cell; vertical-align: middle; }
.conf-val-cell   { display: table-cell; vertical-align: middle; text-align: right;
                   width: 44px; padding-left: 8px; }
.conf-track      { height: 5px; background: var(--surface-alt); border-radius: 2px;
                   overflow: hidden; border: 1px solid var(--border); }
.conf-fill       { height: 100%; border-radius: 2px; background: var(--red); }
.conf-val        { font-family: 'DM Mono', 'Courier New', monospace; font-size: 10px;
                   font-weight: 500; color: var(--text-secondary); }

/* ── Sub-section label ── */
.sub-header { margin: 10px 0 5px; padding-left: 9px; border-left: 3px solid var(--accent); }

/* ── Empty state ── */
.empty { padding: 11px 13px; font-size: 11px; color: var(--text-muted); font-style: italic;
         background: var(--surface); border: 1px dashed var(--border); border-radius: 6px;
         text-align: center; }

/* ── Chart card ── */
.chart-card  { background: var(--surface); border: 1px solid var(--border);
               border-radius: 7px; padding: 14px 16px; margin-bottom: 12px; break-after: page; }
.chart-title { font-size: 11px; font-weight: 700; color: var(--text);
               text-transform: uppercase; letter-spacing: 0.05em;
               margin-bottom: 12px; padding-bottom: 9px; border-bottom: 1px solid var(--border); }

/* ── Footer ── */
.report-footer       { display: table; width: 100%; margin-top: 14px; padding-top: 9px;
                        border-top: 1px solid var(--border); }
.report-footer__left  { display: table-cell; font-size: 9px; color: var(--text-muted);
                         font-weight: 500; letter-spacing: 0.04em; }
.report-footer__right { display: table-cell; font-size: 9px; color: var(--text-muted);
                         font-weight: 500; text-align: right; }
"""

# ──────────────────────────────────────────────────────────────────────────────
# Horizontal Bar Chart — fixed clipping
# LABEL_W  : pixels reserved for category text (left side)
# PAD_T    : top padding must be > font-size of scale labels to avoid clipping
# overflow : visible on SVG so nothing gets cut by viewBox boundary
# ──────────────────────────────────────────────────────────────────────────────

import textwrap

def _build_svg_chart(stats: dict[str, int]) -> str:
    if not stats:
        return ""
    items = list(stats.items())
    
    max_val = max(v for _, v in items) or 1

    # --- Настройки размеров ---
    ROW_H   = 44    # УВЕЛИЧЕНО: чтобы влезло 2 строки текста
    GAP     = 8     # Отступ между рядами
    LABEL_W = 180   # Ширина зоны для текста
    BAR_W   = 420   # Ширина зоны для баров
    VAL_W   = 50    # Ширина для цифр справа
    PAD_L   = 15    # Левый отступ (защита от зарезания)
    PAD_R   = 10    
    PAD_T   = 28    # Верхний отступ для шкалы
    PAD_B   = 10    
    DIVS    = 5     

    n = len(items)
    VW = PAD_L + LABEL_W + BAR_W + VAL_W + PAD_R
    VH = PAD_T + n * (ROW_H + GAP) - GAP + PAD_B
    BAR_X0 = PAD_L + LABEL_W

    COLORS   = ["#2555c8", "#3f6fe0", "#5b8aff", "#7aa3ff", "#9dbdff"]
    GRID_COL = "#e4e7f0"
    LBL_COL  = "#4a5280"
    VAL_COL  = "#1a2040"
    BASE_COL = "#c8cde0"

    svg = [
        f'<svg viewBox="0 0 {VW} {VH}" xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%; height:auto; display:block;" '
        f'shape-rendering="crispEdges" text-rendering="geometricPrecision">'
    ]

    # ── Сетка ──
    for i in range(DIVS + 1):
        x = BAR_X0 + round(i * BAR_W / DIVS)
        gv = round(max_val * i / DIVS)
        col = BASE_COL if i == 0 else GRID_COL
        svg.append(f'<line x1="{x}" y1="{PAD_T - 2}" x2="{x}" y2="{VH - PAD_B}" stroke="{col}" stroke-width="1"/>')
        svg.append(f'<text x="{x}" y="{PAD_T - 10}" text-anchor="middle" font-size="10" fill="{LBL_COL}" font-family="\'DM Sans\',sans-serif">{gv}</text>')

    # ── Ряды ──
    for i, (cat, val) in enumerate(items):
        y_top = PAD_T + i * (ROW_H + GAP)
        y_mid = y_top + (ROW_H // 2)
        
        # Разрезаем текст на строки (примерно по 25 символов)
        wrapped_lines = textwrap.wrap(cat, width=25)
        # Ограничиваем до 2 строк, чтобы не вылезать за пределы ROW_H
        lines = wrapped_lines[:2] 
        
        # Вычисляем Y для текста, чтобы он был центрирован вертикально относительно бара
        # 1.2em ~ 13px при font-size 10.5
        line_height = 13
        total_text_h = len(lines) * line_height
        text_start_y = y_mid - (total_text_h / 2) + 9 # +9 — это компенсация базовой линии шрифта

        # Рисуем текст (каждую строку отдельно через tspan)
        text_element = [f'<text x="{BAR_X0 - 12}" y="{text_start_y}" text-anchor="end" font-size="10.5" fill="{LBL_COL}" font-family="\'DM Sans\',sans-serif" font-weight="500">']
        for j, line in enumerate(lines):
            # Для второй и последующих строк указываем смещение dy
            dy = "1.2em" if j > 0 else "0"
            text_element.append(f'<tspan x="{BAR_X0 - 12}" dy="{dy}">{_html.escape(line)}</tspan>')
        text_element.append('</text>')
        svg.append("".join(text_element))

        # Рисуем бар
        bar_px = round(val / max_val * BAR_W) if max_val else 0
        bar_h  = 20 # Фиксированная высота бара
        bar_y  = y_mid - (bar_h / 2)
        color  = COLORS[i % len(COLORS)]

        if val > 0:
            svg.append(f'<rect x="{BAR_X0}" y="{bar_y}" width="{bar_px}" height="{bar_h}" rx="4" fill="{color}"/>')
            if bar_px > 10: # Блик
                svg.append(f'<rect x="{BAR_X0}" y="{bar_y}" width="{bar_px}" height="4" rx="2" fill="white" opacity="0.15"/>')
        else:
            svg.append(f'<rect x="{BAR_X0}" y="{bar_y}" width="3" height="{bar_h}" rx="1.5" fill="{GRID_COL}"/>')

        # Число
        svg.append(f'<text x="{BAR_X0 + bar_px + 8}" y="{y_mid + 5}" text-anchor="start" font-size="11" font-weight="700" fill="{VAL_COL}" font-family="\'DM Sans\',sans-serif">{val}</text>')

    svg.append('</svg>')
    return "\n".join(svg)

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _e(s: Any) -> str:
    return _html.escape(str(s) if s is not None else "—")


def _build_status_table(rows) -> str:
    if not rows:
        return '<div class="empty">Нет данных</div>'
    rows_html = []
    for i, row in enumerate(rows, 1):
        failed     = getattr(row, "status", "") == "Провалено"
        status_cls = "status-fail" if failed else "status-pass"
        rows_html.append(
            f'<tr>'
            f'<td class="row-num">{i}</td>'
            f'<td style="font-weight:500;">{_e(row.parameter)}</td>'
            f'<td class="{status_cls}">{_e(row.status)}</td>'
            f'<td style="color:var(--text-secondary);">{_e(row.founded)}</td>'
            f'</tr>'
        )
    return (
        f'<div class="card">'
        f'<table class="data-table"><thead><tr>'
        f'<th style="width:36px;">№</th><th>Параметр</th>'
        f'<th style="width:100px;">Статус</th><th>Обнаружено</th>'
        f'</tr></thead><tbody>{"".join(rows_html)}</tbody></table></div>'
    )


def _build_problems_table(rows) -> str:
    if not rows:
        return '<div class="empty">Нарушений не обнаружено</div>'
    rows_html = []
    for row in rows:
        conf = float(getattr(row, "confidence", 0))
        pct  = int(conf * 100)
        rows_html.append(
            f'<tr>'
            f'<td style="font-weight:600;">{_e(row.category)}</td>'
            f'<td class="mono">{_e(row.start_time)}</td>'
            f'<td class="mono">{_e(row.end_time)}</td>'
            f'<td>'
            f'<div class="conf-wrap">'
            f'<div class="conf-track-cell"><div class="conf-track">'
            f'<div class="conf-fill" style="width:{pct}%"></div>'
            f'</div></div>'
            f'<div class="conf-val-cell"><span class="conf-val">{conf:.3f}</span></div>'
            f'</div>'
            f'</td></tr>'
        )
    return (
        f'<div class="card">'
        f'<table class="data-table"><thead><tr>'
        f'<th>Категория</th><th style="width:80px;">Начало</th>'
        f'<th style="width:80px;">Конец</th><th style="width:160px;">Уверенность</th>'
        f'</tr></thead><tbody>{"".join(rows_html)}</tbody></table></div>'
    )


# ──────────────────────────────────────────────────────────────────────────────
# HTML Builder
# ──────────────────────────────────────────────────────────────────────────────

def _build_html(sections, source_info, stats, report_for: str) -> str:
    global_failed = any(s["status"] for s in sections)
    result_cls    = "result-badge--fail" if global_failed else "result-badge--pass"
    result_icon   = "✕" if global_failed else "✓"
    result_label  = "Провалено" if global_failed else "Успешно"

    si = source_info
    meta_items = [
        ("Отчет для",       report_for or "—"),
        ("Источник",        getattr(si, "video_path", "—")),
        ("Дата анализа",    getattr(si, "analysis_timestamp", "—")),
        ("Длительность",    getattr(si, "video_duration_formatted", "—")),
        ("Время обработки", f'{getattr(si, "processing_time_seconds", 0) / 60:.1f} мин'
                            if hasattr(si, "processing_time_seconds") else "—"),
        ("Всего сцен",      getattr(si, "frameCount", "—")),
    ]

    def _mc(k, v):
        return (
            f'<td class="meta-item">'
            f'<div class="meta-item__label">{_e(k)}</div>'
            f'<div class="meta-item__value">{_e(v)}</div>'
            f'</td>'
        )

    r1 = "".join(_mc(k, v) for k, v in meta_items[:3])
    r2 = "".join(_mc(k, v) for k, v in meta_items[3:])
    meta_html = f'<table class="meta-table"><tr>{r1}</tr><tr>{r2}</tr></table>'

    chart_html = ""
    if stats:
        chart_html = (
            f'<div class="chart-card">'
            f'<div class="chart-title">Статистика нарушений по категориям</div>'
            f'{_build_svg_chart(stats)}'
            f'</div>'
        )

    sections_html = ""
    for sec in sections:
        bc = "badge--red" if sec["status"] else "badge--green"
        bl = "Провалено" if sec["status"] else "Успешно"
        sections_html += (
            f'<div class="section">'
            f'<div class="section-header">'
            f'<div class="section-header__left"><span class="heading-md">{_e(sec["title"])}</span></div>'
            f'<div class="section-header__right"><span class="badge {bc}">{bl}</span></div>'
            f'</div>'
            f'<div class="card card--top-flush"><div class="card-inner">'
            + _build_status_table(sec.get("status_table", []))
            + f'<div class="sub-header"><span class="heading-sm">Обнаруженные проблемы</span></div>'
            + _build_problems_table(sec.get("problems_table", []))
            + f'</div></div></div>'
        )

    ts = _e(getattr(si, "analysis_timestamp", ""))

    return f"""<!DOCTYPE html>
<html lang="ru">
<head><meta charset="UTF-8"><style>{_CSS}</style></head>
<body>

<div class="report-header">
  <div class="report-header__left">
    <div class="logo-name">LINZA<span class="logo-dot">.</span>Detector</div>
    <div class="logo-sub">Структурированный отчёт по видеофайлу</div>
  </div>
  <div class="report-header__right">
    <span class="result-badge {result_cls}">{result_icon}&nbsp;&nbsp;{result_label}</span>
  </div>
</div>

{meta_html}
{chart_html}
{sections_html}

<div class="report-footer">
  <div class="report-footer__left">LINZA.Detector — Автоматический анализ видео</div>
  <div class="report-footer__right">{ts}</div>
</div>

</body>
</html>"""


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def generate_pdf(
    filename: str,
    sections: list,
    source_info=None,
    stats: Optional[dict] = None,
    report_for: str = "Система мониторинга",
) -> None:
    from weasyprint import HTML
    html_content = _build_html(sections, source_info, stats, report_for)
    HTML(string=html_content).write_pdf(filename)


def get_html_preview(
    sections: list,
    source_info=None,
    stats: Optional[dict] = None,
    report_for: str = "Система мониторинга",
) -> str:
    return _build_html(sections, source_info, stats, report_for)