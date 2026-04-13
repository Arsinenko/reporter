"""
LINZA.Detector — PDF report generator (Updated with Zebra rows and borders)
"""

from __future__ import annotations

import html as _html
from dataclasses import dataclass
from typing import Any, Optional

# ──────────────────────────────────────────────────────────────────────────────
# CSS
# ──────────────────────────────────────────────────────────────────────────────

_CSS = """
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --linza-bg:              #edf0f8;
  --linza-surface:         rgba(255,255,255,0.82);
  --linza-border:          #d1d5db; /* Сделали границу чуть темнее для четкости */
  --linza-text:            #283050;
  --linza-text-secondary:  #5a6494;
  --linza-text-muted:      #8a90b8;
  --linza-text-heading:    #181e38;
  --linza-blue:            #3a6cd0;
  --linza-green:           #10b981;
  --linza-red:             #ef4444;
  --linza-zebra:           rgba(0, 0, 0, 0.03); /* Цвет для четных строк */
  font-family: 'DM Sans', system-ui, sans-serif;
  color: var(--linza-text);
}

@page {
  size: A4;
  margin: 0;
}

body { 
  background: var(--linza-bg); 
  font-size: 13px; 
  line-height: 1.5; 
  margin: 0; 
  padding: 0;
  width: 100%;
}

.page-wrapper {
  padding: 20px;
  width: 100%;
}

.heading-md { font-size: 14px; font-weight: 700; color: var(--linza-text-heading); }
.heading-sm { font-size: 12px; font-weight: 700; break-after: avoid; }
.mono { font-family: monospace; font-variant-numeric: tabular-nums; }

.card {
  background: var(--linza-surface);
  border: 1px solid var(--linza-border);
  border-radius: 14px;
  padding: 18px 20px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  margin-bottom: 20px;
  width: 100%;
}

.chart-container {
  break-after: page;
  overflow: visible !important;
}

.report-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--linza-border);
}

.logo-name { font-size: 22px; font-weight: 800; color: var(--linza-blue); letter-spacing: -0.04em; }
.logo-sub { font-size: 11px; color: var(--linza-text-secondary); font-weight: 500; }

.td-status-pass { color: var(--linza-green); font-weight: 700; text-transform: uppercase; }
.td-status-fail { color: var(--linza-red);   font-weight: 700; text-transform: uppercase; }

.meta-grid { 
  display: grid; 
  grid-template-columns: repeat(3, 1fr); 
  gap: 10px; 
  margin-bottom: 20px; 
  width: 100%; 
}
.meta-item { background: var(--linza-surface); border: 1px solid var(--linza-border); border-radius: 10px; padding: 12px 14px; }
.meta-item__label { font-size: 10px; font-weight: 600; color: var(--linza-text-muted); text-transform: uppercase; margin-bottom: 4px; }
.meta-item__value { font-size: 12px; font-weight: 600; word-break: break-all; color: var(--linza-text-heading); }

.section { margin-bottom: 24px; width: 100%; }
.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; break-after: avoid; }

.badge { padding: 3px 9px; border-radius: 16px; font-size: 10px; font-weight: 600; border: 1px solid transparent; }
.badge--green { background: rgba(16,185,129,0.08); border-color: rgba(16,185,129,0.18); color: var(--linza-green); }
.badge--red   { background: rgba(239,68,68,0.07);  border-color: rgba(239,68,68,0.15);  color: var(--linza-red); }

/* --- ОБНОВЛЕННЫЕ ТАБЛИЦЫ --- */
table { 
  width: 100%; 
  border-collapse: collapse; 
  font-size: 11px; 
  border: 1px solid var(--linza-border); /* Внешняя рамка таблицы */
}

th { 
  background: rgba(0,0,0,0.05); 
  color: var(--linza-text-secondary); 
  font-size: 10px; 
  padding: 8px 10px; 
  text-align: left; 
  text-transform: uppercase; 
  border-right: 1px solid var(--linza-border);
  border-bottom: 2px solid var(--linza-border);
}

td { 
  padding: 7px 10px; 
  border-bottom: 1px solid var(--linza-border); 
  border-right: 1px solid var(--linza-border); /* Вертикальные границы */
}

/* Убираем последнюю правую границу, чтобы не дублировать рамку карточки */
th:last-child, td:last-child {
  border-right: none;
}

/* Чередование строк (Зебра) */
tbody tr:nth-child(even) {
  background-color: var(--linza-zebra);
}

/* Подсветка при наведении (опционально, полезно для HTML-просмотра) */
tbody tr:hover {
  background-color: rgba(58, 108, 208, 0.05);
}

.confidence-bar-track { flex: 1; height: 5px; background: rgba(0,0,0,0.06); border-radius: 4px; overflow: hidden; }
.confidence-bar-fill { height: 100%; background: var(--linza-red); }

.spacer-sm { height: 8px; }
"""

# ──────────────────────────────────────────────────────────────────────────────
# SVG Chart Logic (без изменений)
# ──────────────────────────────────────────────────────────────────────────────

def _build_svg_chart(stats: dict[str, int]) -> str:
    if not stats: return ""
    categories = list(stats.keys())
    values = list(stats.values())
    max_val = max(values) if values else 1
    
    W, H = 800, 550 
    pL, pR, pT, pB = 60, 150, 30, 300 
    chart_w, chart_h = W - pL - pR, H - pT - pB
    n = len(categories)
    gap = 18
    bar_w = max(20, (chart_w - gap * (n + 1)) // n)

    svg = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" style="width:100%; height:auto; overflow:visible;">']
    
    for i in range(6):
        y = pT + chart_h - i * chart_h // 5
        gv = round(max_val * i / 5)
        svg.append(f'<line x1="{pL}" y1="{y}" x2="{W-pR}" y2="{y}" stroke="#e2e5ef" stroke-width="1"/>')
        svg.append(f'<text x="{pL-10}" y="{y+4}" text-anchor="end" font-size="11" fill="#8a90b8" font-family="sans-serif">{gv}</text>')

    for i, (cat, val) in enumerate(zip(categories, values)):
        bw_h = int(val / max_val * chart_h) if max_val else 0
        x = pL + gap + i * (bar_w + gap)
        y = pT + chart_h - bw_h
        
        svg.append(f'<rect x="{x}" y="{y}" width="{bar_w}" height="{bw_h}" rx="3" fill="#3a6cd0" opacity="0.8"/>')
        svg.append(f'<text x="{x + bar_w//2}" y="{y-6}" text-anchor="middle" font-size="11" font-weight="700" fill="#283050" font-family="sans-serif">{val}</text>')
        
        lx = x + bar_w // 2
        ly = pT + chart_h + 12
        svg.append(
            f'<text transform="rotate(60, {lx}, {ly})" x="{lx}" y="{ly}" '
            f'font-size="10" fill="#5a6494" text-anchor="start" font-family="sans-serif">{_html.escape(cat)}</text>'
        )

    svg.append('</svg>')
    return "\n".join(svg)

# ──────────────────────────────────────────────────────────────────────────────
# Logic
# ──────────────────────────────────────────────────────────────────────────────

def _e(s: Any) -> str:
    return _html.escape(str(s) if s is not None else "")

def _build_status_table(rows) -> str:
    rows_html = []
    for i, row in enumerate(rows, 1):
        failed = getattr(row, "status", "") == "Провалено"
        # Класс row-fail/pass можно использовать для специфической окраски текста, 
        # но зебра будет работать поверх фона через CSS
        status_cls = "td-status-fail" if failed else "td-status-pass"
        rows_html.append(
            f'<tr>'
            f'<td style="width:30px; text-align:center;">{i}</td>'
            f'<td>{_e(row.parameter)}</td>'
            f'<td class="{status_cls}">{_e(row.status)}</td>'
            f'<td>{_e(row.founded)}</td>'
            f'</tr>'
        )
    return f'<div class="card" style="padding:0; overflow:hidden;"><table><thead><tr><th>№</th><th>Параметр</th><th>Статус</th><th>Обнаружено</th></tr></thead><tbody>{"".join(rows_html)}</tbody></table></div>'

def _build_problems_table(rows) -> str:
    if not rows: return '<p style="font-size:11px;color:var(--linza-text-muted);padding:5px;">Нарушений не обнаружено</p>'
    rows_html = []
    for row in rows:
        conf = float(getattr(row, "confidence", 0))
        rows_html.append(
            f'<tr>'
            f'<td>{_e(row.category)}</td>'
            f'<td class="mono">{_e(row.start_time)}</td>'
            f'<td class="mono">{_e(row.end_time)}</td>'
            f'<td>'
            f'<div style="display:flex;align-items:center;gap:8px;">'
            f'<div class="confidence-bar-track"><div class="confidence-bar-fill" style="width:{int(conf*100)}%"></div></div>'
            f'<span style="font-size:10px;font-weight:600;">{conf:.3f}</span>'
            f'</div>'
            f'</td>'
            f'</tr>'
        )
    return f'<div class="card" style="padding:0; overflow:hidden;"><table><thead><tr><th>Категория</th><th>Начало</th><th>Конец</th><th>Уверенность</th></tr></thead><tbody>{"".join(rows_html)}</tbody></table></div>'

def _build_html(sections, source_info, stats, report_for: str) -> str:
    global_failed = any(s["status"] for s in sections)
    header_status_cls = "td-status-fail" if global_failed else "td-status-pass"
    result_label = "Провалено" if global_failed else "Успешно"

    si = source_info
    meta_items = [
        ("Отчет для", report_for or "—"),
        ("Источник", getattr(si, "video_path", "—")),
        ("Дата анализа", getattr(si, "analysis_timestamp", "—")),
        ("Длительность", getattr(si, "video_duration_formatted", "—")),
        ("Время обработки", f'{getattr(si, "processing_time_seconds", 0) / 60:.1f} мин' if hasattr(si, "processing_time_seconds") else "—"),
        ("Всего сцен", getattr(si, "frameCount", "—")),
    ]
    meta_html = "".join(f'<div class="meta-item"><div class="meta-item__label">{_e(k)}</div><div class="meta-item__value">{_e(v)}</div></div>' for k, v in meta_items)

    chart_html = ""
    if stats:
        chart_html = (
            f'<div class="card chart-container">'
            f'<div class="heading-sm" style="margin-bottom:15px; color:var(--linza-text-heading);">Статистика нарушений по категориям</div>'
            f'{_build_svg_chart(stats)}'
            f'</div>'
        )

    sections_html = ""
    for sec in sections:
        badge_cls = "badge--red" if sec["status"] else "badge--green"
        badge_label = "Провалено" if sec["status"] else "Успешно"
        sections_html += (
            f'<div class="section"><div class="section-header"><span class="heading-md">{_e(sec["title"])}</span><span class="badge {badge_cls}">{badge_label}</span></div>'
            + _build_status_table(sec.get("status_table", []))
            + '<div class="spacer-sm"></div><div class="heading-sm" style="margin-bottom:6px;">Обнаруженные проблемы</div>'
            + _build_problems_table(sec.get("problems_table", []))
            + '</div>'
        )

    return f"""<!DOCTYPE html>
<html lang="ru"><head><meta charset="UTF-8"><style>{_CSS}</style></head>
<body>
  <div class="page-wrapper">
    <div class="report-header">
      <div class="logo-block">
        <span class="logo-name">LINZA.Detector</span><br>
        <span class="logo-sub">Структурированный отчет по видеофайлу</span>
      </div>
      <div class="{header_status_cls}" style="font-size: 16px;">{result_label.upper()}</div>
    </div>
    <div class="meta-grid">{meta_html}</div>
    {chart_html}
    {sections_html}
  </div>
</body></html>"""

def generate_pdf(filename: str, sections: list, source_info=None, stats: Optional[dict] = None, report_for: str = "Система мониторинга") -> None:
    from weasyprint import HTML
    html_content = _build_html(sections, source_info, stats, report_for)
    HTML(string=html_content).write_pdf(filename)