from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus.flowables import Flowable
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io

# =======================
# ШРИФТЫ
# =======================
pdfmetrics.registerFont(TTFont("DejaVu", "fonts/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", "fonts/DejaVuSans-Bold.ttf"))

# =======================
# ЦВЕТА — Dashboard Dark Header
# =======================
DARK_NAVY    = colors.HexColor("#0F1C2E")   # Шапка / сайдбар
ACCENT_BLUE  = colors.HexColor("#1565C0")   # Акцент заголовков секций
ACCENT_TEAL  = colors.HexColor("#00838F")   # Вторичный акцент / линии
MID_GREY     = colors.HexColor("#455A64")   # Вспомогательный текст
LIGHT_GREY   = colors.HexColor("#ECEFF1")   # Фоны строк таблиц
WHITE        = colors.HexColor("#FFFFFF")

# Статусы
STATUS_FAIL_BG   = colors.HexColor("#FFEBEE")
STATUS_FAIL_TEXT = colors.HexColor("#B71C1C")
STATUS_OK_BG     = colors.HexColor("#E8F5E9")
STATUS_OK_TEXT   = colors.HexColor("#1B5E20")
STATUS_FAIL_DOT  = colors.HexColor("#E53935")
STATUS_OK_DOT    = colors.HexColor("#43A047")

# KPI-карточки
KPI_BG_TOTAL     = colors.HexColor("#E3F2FD")
KPI_BG_FAIL      = colors.HexColor("#FFEBEE")
KPI_BG_PASS      = colors.HexColor("#E8F5E9")
KPI_BG_TIME      = colors.HexColor("#F3E5F5")

PAGE_WIDTH = 170 * mm


# =======================
# КАСТОМНЫЙ FLOWABLE — горизонтальная цветная линия
# =======================
class ColorLine(Flowable):
    def __init__(self, width, color, thickness=1):
        Flowable.__init__(self)
        self.width = width
        self.color = color
        self.thickness = thickness
        self.height = thickness

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)


# =======================
# СТИЛИ
# =======================
base_styles = getSampleStyleSheet()

styles = {
    "header_title": ParagraphStyle(
        "header_title",
        fontName="DejaVu-Bold",
        fontSize=20,
        leading=24,
        textColor=WHITE,
        spaceAfter=2,
    ),
    "header_sub": ParagraphStyle(
        "header_sub",
        fontName="DejaVu",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#90CAF9"),
    ),
    "section_title": ParagraphStyle(
        "section_title",
        fontName="DejaVu-Bold",
        fontSize=11,
        leading=14,
        textColor=WHITE,
        spaceAfter=0,
    ),
    "kpi_value": ParagraphStyle(
        "kpi_value",
        fontName="DejaVu-Bold",
        fontSize=22,
        leading=26,
        alignment=TA_CENTER,
        textColor=DARK_NAVY,
    ),
    "kpi_label": ParagraphStyle(
        "kpi_label",
        fontName="DejaVu",
        fontSize=7,
        leading=9,
        alignment=TA_CENTER,
        textColor=MID_GREY,
    ),
    "meta_label": ParagraphStyle(
        "meta_label",
        fontName="DejaVu",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#78909C"),
    ),
    "meta_value": ParagraphStyle(
        "meta_value",
        fontName="DejaVu-Bold",
        fontSize=8,
        leading=11,
        textColor=DARK_NAVY,
    ),
    "normal": ParagraphStyle(
        "normal",
        fontName="DejaVu",
        fontSize=8,
        leading=11,
        textColor=DARK_NAVY,
    ),
    "table_header": ParagraphStyle(
        "table_header",
        fontName="DejaVu-Bold",
        fontSize=7,
        leading=9,
        textColor=WHITE,
    ),
    "subheading": ParagraphStyle(
        "subheading",
        fontName="DejaVu-Bold",
        fontSize=9,
        leading=11,
        textColor=DARK_NAVY,
        spaceBefore=8,
        spaceAfter=4,
    ),
    "problems_title": ParagraphStyle(
        "problems_title",
        fontName="DejaVu-Bold",
        fontSize=8,
        leading=10,
        textColor=STATUS_FAIL_TEXT,
    ),
}


# =======================
# ШАПКА СТРАНИЦЫ (canvas)
# =======================
HEADER_HEIGHT = 28 * mm

def draw_page_header(canvas, doc, title="LINZA.Detector", subtitle="Структурированный отчет по видеофайлу"):
    """Рисует тёмную шапку на каждой странице."""
    w, h = A4
    canvas.saveState()

    # Тёмный прямоугольник
    canvas.setFillColor(DARK_NAVY)
    canvas.rect(0, h - HEADER_HEIGHT, w, HEADER_HEIGHT, fill=1, stroke=0)

    # Акцентная полоска снизу шапки
    canvas.setFillColor(ACCENT_TEAL)
    canvas.rect(0, h - HEADER_HEIGHT, w, 2, fill=1, stroke=0)

    # Текст
    canvas.setFillColor(WHITE)
    canvas.setFont("DejaVu-Bold", 18)
    canvas.drawString(15 * mm, h - 17 * mm, title)

    canvas.setFillColor(colors.HexColor("#90CAF9"))
    canvas.setFont("DejaVu", 8)
    canvas.drawString(15 * mm, h - 23 * mm, subtitle)

    # Номер страницы справа
    canvas.setFillColor(colors.HexColor("#90CAF9"))
    canvas.setFont("DejaVu", 7)
    page_text = f"стр. {canvas.getPageNumber()}"
    canvas.drawRightString(w - 15 * mm, h - 17 * mm, page_text)

    canvas.restoreState()


# =======================
# KPI-КАРТОЧКИ
# =======================
def build_kpi_row(total_scenes, failed_count, passed_count, processing_time):
    """Строит строку из 4 KPI-карточек."""
    def kpi_cell(value, label, bg_color):
        return [
            Paragraph(str(value), styles["kpi_value"]),
            Paragraph(label, styles["kpi_label"]),
        ]

    card_w = 40 * mm
    inner_pad = 4 * mm

    # Каждая карточка — вложенная таблица
    def make_card(value, label, bg):
        cell_data = [
            [Paragraph(str(value), styles["kpi_value"])],
            [Paragraph(label, styles["kpi_label"])],
        ]
        t = Table(cell_data, colWidths=[card_w - 2 * inner_pad])
        t.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("BACKGROUND", (0, 0), (-1, -1), bg),
            ("ROUNDEDCORNERS", [4, 4, 4, 4]),
        ]))
        return t

    cards = [
        make_card(total_scenes, "ВСЕГО СЦЕН", KPI_BG_TOTAL),
        make_card(failed_count,  "НАРУШЕНИЙ",  KPI_BG_FAIL),
        make_card(passed_count,  "ПРОВЕРОК OK", KPI_BG_PASS),
        make_card(f"{processing_time}с", "ВРЕМЯ ОБРАБОТКИ", KPI_BG_TIME),
    ]

    row = Table(
        [cards],
        colWidths=[card_w] * 4,
        rowHeights=[22 * mm],
    )
    row.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]))
    return row


# =======================
# МЕТА-ИНФОРМАЦИЯ
# =======================
def build_meta_table(source_info):
    data = [
        ["ИСТОЧНИК",         source_info.video_path],
        ["ДЛИТЕЛЬНОСТЬ",     source_info.video_duration_formatted],
        ["ДАТА АНАЛИЗА",     source_info.analysis_timestamp],
        ["ВРЕМЯ ОБРАБОТКИ",  f"{source_info.processing_time_seconds / 60:.1f} минут"],
    ]

    table_data = []
    for label, value in data:
        table_data.append([
            Paragraph(label, styles["meta_label"]),
            Paragraph(value, styles["meta_value"]),
        ])

    t = Table(table_data, colWidths=[38 * mm, 122 * mm])
    t.setStyle(TableStyle([
        ("ALIGN",  (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, LIGHT_GREY),
    ]))
    return t


# =======================
# ПЛАШКА ОБЩЕГО СТАТУСА
# =======================
def build_global_status_banner(has_violations):
    if has_violations:
        bg    = STATUS_FAIL_BG
        text  = "⚠  ТЕСТ ПРОВАЛЕН"
        color = STATUS_FAIL_TEXT
    else:
        bg    = STATUS_OK_BG
        text  = "✓  ТЕСТ ПРОЙДЕН"
        color = STATUS_OK_TEXT

    style = ParagraphStyle(
        "banner",
        fontName="DejaVu-Bold",
        fontSize=11,
        leading=14,
        textColor=color,
        alignment=TA_CENTER,
    )
    t = Table(
        [[Paragraph(text, style)]],
        colWidths=[PAGE_WIDTH],
        rowHeights=[12 * mm],
    )
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("ALIGN",  (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
        ("BOX", (0, 0), (-1, -1), 1, color),
    ]))
    return t


# =======================
# ЗАГОЛОВОК СЕКЦИИ (тёмная полоска)
# =======================
def build_section_header(title, status_bool):
    status_text = "ПРОВАЛЕНО" if status_bool else "УСПЕШНО"
    status_bg   = STATUS_FAIL_DOT if status_bool else STATUS_OK_DOT

    left = Paragraph(title.upper(), styles["section_title"])

    # Маленький бейдж статуса
    badge_style = ParagraphStyle(
        "badge",
        fontName="DejaVu-Bold",
        fontSize=7,
        leading=9,
        textColor=WHITE,
        alignment=TA_CENTER,
    )
    right = Table(
        [[Paragraph(status_text, badge_style)]],
        colWidths=[22 * mm],
        rowHeights=[5 * mm],
    )
    right.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), status_bg),
        ("ALIGN",  (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROUNDEDCORNERS", [3, 3, 3, 3]),
    ]))

    row = Table(
        [[left, right]],
        colWidths=[PAGE_WIDTH - 25 * mm, 25 * mm],
        rowHeights=[9 * mm],
    )
    row.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ACCENT_BLUE),
        ("ALIGN",  (0, 0), (0, 0), "LEFT"),
        ("ALIGN",  (1, 0), (1, 0), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (0, 0), 8),
        ("RIGHTPADDING", (1, 0), (1, 0), 6),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    return row


# =======================
# ТАБЛИЦА СТАТУСОВ
# =======================
def build_status_table(data):
    header = [
        Paragraph("№",         styles["table_header"]),
        Paragraph("Параметр",  styles["table_header"]),
        Paragraph("Статус",    styles["table_header"]),
        Paragraph("Обнаружено",styles["table_header"]),
    ]
    table_data = [header]

    for i, row in enumerate(data, 1):
        table_data.append([
            Paragraph(str(i), styles["normal"]),
            Paragraph(row.parameter, styles["normal"]),
            Paragraph(row.status, styles["normal"]),
            Paragraph(row.founded, styles["normal"]),
        ])

    col_widths = [8 * mm, 85 * mm, 38 * mm, 39 * mm]
    t = Table(table_data, colWidths=col_widths, repeatRows=1)

    style_cmds = [
        # Заголовок
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT_BLUE),
        ("FONTNAME",   (0, 0), (-1, 0), "DejaVu-Bold"),
        ("FONTSIZE",   (0, 0), (-1, 0), 7),
        # Тело
        ("FONTNAME",   (0, 1), (-1, -1), "DejaVu"),
        ("FONTSIZE",   (0, 1), (-1, -1), 7),
        ("GRID",       (0, 0), (-1, -1), 0.3, colors.HexColor("#CFD8DC")),
        ("ALIGN",      (0, 0), (-1, -1), "LEFT"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        # Зебра (чётные строки)
        *[("BACKGROUND", (0, i), (-1, i), LIGHT_GREY)
          for i in range(2, len(table_data), 2)],
    ]

    # Цветной статус в ячейках
    for i, row in enumerate(data, 1):
        if row.status == "Провалено":
            style_cmds.append(("BACKGROUND",  (2, i), (3, i), STATUS_FAIL_BG))
            style_cmds.append(("TEXTCOLOR",   (2, i), (3, i), STATUS_FAIL_TEXT))
            style_cmds.append(("FONTNAME",    (2, i), (3, i), "DejaVu-Bold"))
        else:
            style_cmds.append(("BACKGROUND",  (2, i), (3, i), STATUS_OK_BG))
            style_cmds.append(("TEXTCOLOR",   (2, i), (3, i), STATUS_OK_TEXT))

    t.setStyle(TableStyle(style_cmds))
    return t


# =======================
# ТАБЛИЦА ПРОБЛЕМ
# =======================
def build_problems_table(data):
    header = [
        Paragraph("Категория",   styles["table_header"]),
        Paragraph("Начало",      styles["table_header"]),
        Paragraph("Конец",       styles["table_header"]),
        Paragraph("Уверенность", styles["table_header"]),
    ]
    table_data = [header]

    for row in data:
        table_data.append([
            Paragraph(row.category, styles["normal"]),
            Paragraph(row.start_time, styles["normal"]),
            Paragraph(row.end_time, styles["normal"]),
            Paragraph(f"{row.confidence:.3f}", styles["normal"]),
        ])

    col_widths = [75 * mm, 32 * mm, 32 * mm, 31 * mm]
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), MID_GREY),
        ("FONTNAME",      (0, 0), (-1, 0), "DejaVu-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 7),
        ("FONTNAME",      (0, 1), (-1, -1), "DejaVu"),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#CFD8DC")),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND",    (0, 1), (-1, -1), STATUS_FAIL_BG),
        ("TEXTCOLOR",     (0, 1), (-1, -1), STATUS_FAIL_TEXT),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


# =======================
# СЕКЦИЯ
# =======================
def render_section(elements, section):
    # 1. Группируем заголовок и статусную таблицу
    status_block = [
        Spacer(1, 8),
        build_section_header(section["title"], section["status"]),
        Spacer(1, 4),
        build_status_table(section["status_table"])
    ]
    
    # Оборачиваем их в KeepTogether и добавляем в основной список
    elements.append(KeepTogether(status_block))

    # 2. Остальное добавляем как обычно (может переноситься отдельно)
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("Обнаруженные нарушения", styles["subheading"]))
    elements.append(ColorLine(PAGE_WIDTH, ACCENT_TEAL, thickness=1))
    elements.append(Spacer(1, 3))
    elements.append(build_problems_table(section["problems_table"]))


# =======================
# ГОРИЗОНТАЛЬНЫЙ БАР-ЧАРТ (matplotlib)
# =======================
def build_stats_chart(stats):
    if not stats:
        return None

    from matplotlib import font_manager
    font_path = "fonts/DejaVuSans.ttf"
    font_prop = font_manager.FontProperties(fname=font_path)

    categories = list(stats.keys())
    values     = list(stats.values())

    # Горизонтальный бар — лучше читается при длинных названиях
    fig, ax = plt.subplots(figsize=(8, max(3, len(categories) * 0.55)))
    fig.patch.set_facecolor('#F8FAFB')

    bar_colors = ['#1565C0' if v == max(values) else '#90CAF9' for v in values]
    bars = ax.barh(categories, values, color=bar_colors, edgecolor='none',
                   height=0.55, zorder=3)

    ax.set_facecolor('#F8FAFB')
    ax.xaxis.grid(True, linestyle='--', alpha=0.4, color='#B0BEC5', zorder=0)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(axis='y', length=0)

    ax.set_title("Статистика нарушений по категориям",
                 fontproperties=font_prop, fontsize=10,
                 color='#0F1C2E', pad=12, loc='left', fontweight='bold')

    plt.xticks(fontsize=7, color='#455A64')
    plt.yticks(fontproperties=font_prop, fontsize=8, color='#0F1C2E')

    # Подписи значений
    for bar in bars:
        w = bar.get_width()
        ax.text(w + 0.1, bar.get_y() + bar.get_height() / 2,
                str(int(w)), va='center', ha='left',
                fontproperties=font_prop, fontsize=8,
                color='#1565C0', fontweight='bold')

    plt.tight_layout(pad=1.5)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=400, bbox_inches='tight', transparent=False)
    buf.seek(0)
    plt.close(fig)

    desired_width = 160 * mm
    img = Image(buf)
    img.drawWidth  = desired_width
    img.drawHeight = desired_width * (fig.get_figheight() / fig.get_figwidth())
    img.hAlign = 'CENTER'
    return img


# =======================
# FOOTER (canvas)
# =======================
# def draw_footer(canvas, doc):
#     w, _ = A4
#     canvas.saveState()
#     canvas.setFillColor(DARK_NAVY)
#     canvas.rect(0, 0, w, 8 * mm, fill=1, stroke=0)
#     canvas.setFillColor(colors.HexColor("#546E7A"))
#     canvas.setFont("DejaVu", 6)
#     canvas.drawCentredString(w / 2, 2.5 * mm, "LINZA.Detector — Автоматизированный анализ видеоконтента")
#     canvas.restoreState()


def on_page(canvas, doc):
    draw_page_header(canvas, doc)
    # draw_footer(canvas, doc)


# =======================
# ГЕНЕРАЦИЯ PDF
# =======================
def generate_pdf(filename, sections, source_info=None, stats: dict = None):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=HEADER_HEIGHT + 6 * mm,   # отступ под шапку
        bottomMargin=12 * mm,
    )
    elements = []

    # --- META INFO ---
    elements.append(Spacer(1, 4))
    if source_info:
        elements.append(build_meta_table(source_info))
    elements.append(Spacer(1, 8))

    # --- KPI КАРТОЧКИ ---
    if source_info and stats is not None:
        total   = source_info.frameCount
        failed  = sum(stats.values())
        passed  = total - failed if total > failed else 0
        t_proc  = source_info.processing_time_seconds
        # elements.append(build_kpi_row(total, failed, passed, t_proc))
        elements.append(Spacer(1, 10))

    # --- ОБЩИЙ СТАТУС ---
    global_status = any(section["status"] for section in sections)
    elements.append(build_global_status_banner(global_status))
    elements.append(Spacer(1, 10))

    # --- ГРАФИК ---
    if stats:
        chart = build_stats_chart(stats)
        if chart:
            elements.append(chart)
            elements.append(Spacer(1, 8))
            elements.append(PageBreak())

    # --- СЕКЦИИ ---
    for section in sections:
        render_section(elements, section)

    doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)