"""
LINZA.Detector — PDF report generator
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
  --linza-border:          rgba(0,0,0,0.07);
  --linza-text:            #283050;
  --linza-text-secondary:  #5a6494;
  --linza-text-muted:      #8a90b8;
  --linza-text-heading:    #181e38;
  --linza-blue:            #3a6cd0;
  --linza-green:           #10b981;
  --linza-red:             #ef4444;
  font-family: 'DM Sans', system-ui, sans-serif;
  color: var(--linza-text);
}

@page {
  size: A4;
  margin: 14mm 15mm 18mm 15mm;
  @bottom-center {
    content: "Страница " counter(page) " из " counter(pages);
    font-size: 9px;
    color: var(--linza-text-muted);
  }
}

body { background: var(--linza-bg); font-size: 13px; line-height: 1.5; }

.heading-md { font-size: 14px; font-weight: 700; color: var(--linza-text-heading); }
.heading-sm { font-size: 12px; font-weight: 700; break-after: avoid; }
.mono { font-family: monospace; font-variant-numeric: tabular-nums; }

.card {
  background: var(--linza-surface);
  border: 1px solid var(--linza-border);
  border-radius: 14px;
  padding: 18px 20px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  position: relative;
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

/* Стили статусов (общие для таблицы и заголовка) */
.td-status-pass { color: var(--linza-green); font-weight: 700; }
.td-status-fail { color: var(--linza-red);   font-weight: 700; }

.meta-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 20px; }
.meta-item { background: var(--linza-surface); border: 1px solid var(--linza-border); border-radius: 10px; padding: 12px 14px; }
.meta-item__label { font-size: 10px; font-weight: 600; color: var(--linza-text-muted); text-transform: uppercase; margin-bottom: 4px; }
.meta-item__value { font-size: 13px; font-weight: 600; word-break: break-all; }

.section { margin-bottom: 24px; }
.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; break-after: avoid; }

.badge { padding: 3px 9px; border-radius: 16px; font-size: 10px; font-weight: 600; border: 1px solid transparent; }
.badge--green { background: rgba(16,185,129,0.08); border-color: rgba(16,185,129,0.18); color: var(--linza-green); }
.badge--red   { background: rgba(239,68,68,0.07);  border-color: rgba(239,68,68,0.15);  color: var(--linza-red); }

table { width: 100%; border-collapse: collapse; font-size: 11px; }
th { background: rgba(0,0,0,0.03); color: var(--linza-text-secondary); font-size: 10px; padding: 7px 10px; text-align: left; }
td { padding: 7px 10px; border-bottom: 1px solid var(--linza-border); }
.row-pass td { background: rgba(16,185,129,0.03); }
.row-fail td { background: rgba(239,68,68,0.03); }

.confidence-bar-track { flex: 1; height: 5px; background: rgba(0,0,0,0.06); border-radius: 4px; overflow: hidden; }
.confidence-bar-fill { height: 100%; background: var(--linza-red); }

.spacer-sm { height: 8px; }
"""

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _e(s: Any) -> str:
    return _html.escape(str(s) if s is not None else "")

def _build_status_table(rows) -> str:
    rows_html = []
    for i, row in enumerate(rows, 1):
        failed = getattr(row, "status", "") == "Провалено"
        cls = "row-fail" if failed else "row-pass"
        status_cls = "td-status-fail" if failed else "td-status-pass"
        rows_html.append(
            f'<tr class="{cls}">'
            f'<td style="width:30px;">{i}</td>'
            f'<td>{_e(row.parameter)}</td>'
            f'<td class="{status_cls}">{_e(row.status)}</td>'
            f'<td>{_e(row.founded)}</td>'
            f'</tr>'
        )
    return f'<div class="card" style="padding:0;"><table><thead><tr><th>№</th><th>Параметр</th><th>Статус</th><th>Обнаружено</th></tr></thead><tbody>{"".join(rows_html)}</tbody></table></div>'

def _build_problems_table(rows) -> str:
    if not rows: return '<p style="font-size:11px;color:var(--linza-text-muted);">Нарушений не обнаружено</p>'
    rows_html = []
    for row in rows:
        conf = float(getattr(row, "confidence", 0))
        rows_html.append(
            f'<tr class="row-fail"><td>{_e(row.category)}</td><td class="mono">{_e(row.start_time)}</td><td class="mono">{_e(row.end_time)}</td>'
            f'<td><div style="display:flex;align-items:center;gap:8px;"><div class="confidence-bar-track"><div class="confidence-bar-fill" style="width:{int(conf*100)}%"></div></div>'
            f'<span style="font-size:10px;font-weight:600;">{conf:.3f}</span></div></td></tr>'
        )
    return f'<div class="card" style="padding:0;"><table><thead><tr><th>Категория</th><th>Начало</th><th>Конец</th><th>Уверенность</th></tr></thead><tbody>{"".join(rows_html)}</tbody></table></div>'

# ──────────────────────────────────────────────────────────────────────────────
# Основной строитель HTML
# ──────────────────────────────────────────────────────────────────────────────

def _build_html(sections, source_info, stats) -> str:
    # Определяем глобальный статус
    global_failed = any(s["status"] for s in sections)
    
    # ПРИМЕНЯЕМ СТИЛЬ КАК В ТАБЛИЦЕ
    header_status_cls = "td-status-fail" if global_failed else "td-status-pass"
    result_label = "ПРОВАЛЕНО" if global_failed else "УСПЕШНО"

    si = source_info
    meta_items = [
        ("Источник", getattr(si, "video_path", "—")),
        ("Длительность", getattr(si, "video_duration_formatted", "—")),
        ("Дата анализа", getattr(si, "analysis_timestamp", "—")),
        ("Время обработки", f'{getattr(si, "processing_time_seconds", 0) / 60:.1f} мин'),
        ("Всего сцен", getattr(si, "frameCount", "—")),
        ("Итог", result_label),
    ]
    
    meta_html = "".join(f'<div class="meta-item"><div class="meta-item__label">{_e(k)}</div><div class="meta-item__value">{_e(v)}</div></div>' for k, v in meta_items)

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
<html lang="ru">
<head><meta charset="UTF-8"><style>{_CSS}</style></head>
<body>
  <div class="report-header">
    <div class="logo-block">
      <span class="logo-name">LINZA.Detector</span><br>
      <span class="logo-sub">Структурированный отчет по видеофайлу</span>
    </div>
    <!-- ИСПОЛЬЗУЕМ КЛАСС ИЗ ТАБЛИЦЫ ДЛЯ ЗАГОЛОВКА -->
    <div class="{header_status_cls}" style="font-size: 16px; letter-spacing: 0.05em; text-align: right;">
      {result_label}
    </div>
  </div>
  <div class="meta-grid">{meta_html}</div>
  {sections_html}
</body>
</html>"""

def generate_pdf(filename: str, sections: list, source_info=None, stats: Optional[dict] = None) -> None:
    from weasyprint import HTML
    html_content = _build_html(sections, source_info, stats)
    HTML(string=html_content).write_pdf(filename)
    print(f"[generate_pdf] Сохранено → {filename}")