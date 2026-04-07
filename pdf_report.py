from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, PageBreak
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import matplotlib.pyplot as plt
from reportlab.platypus import Image  # Добавляем импорт Image
from reportlab.lib.enums import TA_CENTER

# =======================
# ШРИФТЫ И ЦВЕТА
# =======================
# Регистрируем обычный и жирный шрифт
pdfmetrics.registerFont(TTFont("DejaVu", "fonts/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", "fonts/DejaVuSans-Bold.ttf"))

# Новые "воздушные" цвета (нежно-зеленый и нежно-розовый)
SOFT_GREEN = colors.HexColor("#dbffdb")    # Почти белый с оттенком мяты
SOFT_RED = colors.HexColor("#ffdbdb")      # Очень бледный розовый
TEXT_GREEN = colors.HexColor("#2E7D32")    # Темно-зеленый для текста
TEXT_RED = colors.HexColor("#C62828")      # Темно-красный для текста

# =======================
# СТИЛИ
# =======================
base_styles = getSampleStyleSheet()

styles = {
    "title": ParagraphStyle(
        "title",
        parent=base_styles["Title"],
        fontName="DejaVu-Bold", # Жирный заголовок
        fontSize=14,
        leading=16,
    ),
    "normal": ParagraphStyle(
        "normal",
        parent=base_styles["Normal"],
        fontName="DejaVu",
        fontSize=10,
        leading=12,
    ),
    "heading": ParagraphStyle(
        "heading",
        parent=base_styles["Heading2"],
        fontName="DejaVu-Bold",
        fontSize=14,
        leading=13,
    ),
    "subheading": ParagraphStyle(
        "subheading",
        parent=base_styles["Heading3"],
        fontName="DejaVu-Bold",
        fontSize=9,
        leading=11,
    ),
    "centered": ParagraphStyle(
        "centered",
        parent=base_styles["Normal"],
        fontName="DejaVu",
        fontSize=10,
        leading=12,
        alignment=TA_CENTER,
    ),

}

PAGE_WIDTH = 170 * mm

# =======================
# ТАБЛИЦЫ
# =======================

def build_status_table(data):
    table_data = [["№", "Параметр", "Статус", "Обнаружено"]]

    for i, row in enumerate(data, 1):
        table_data.append([
            str(i),
            Paragraph(row.parameter, styles["normal"]),
            row.status,
            row.founded
        ])

    col_widths = [10*mm, 85*mm, 35*mm, 40*mm]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)

    style = [
        ("FONTNAME", (0, 0), (-1, -1), "DejaVu"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        # Делаем заголовок жирным
        ("FONTNAME", (0, 0), (-1, 0), "DejaVu-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey), # Сделали сетку чуть светлее (grey вместо black)
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]

    for i, row in enumerate(data, 1):
        if row.status == "Провалено":
            target_color = SOFT_RED
        else:
            target_color = SOFT_GREEN
        
        # Красим только ячейки статуса и результата
        style.append(("BACKGROUND", (2, i), (3, i), target_color))

    table.setStyle(TableStyle(style))
    return table


def build_problems_table(data):
    table_data = [["Категория", "Начало", "Конец", "Уверенность"]]

    for row in data:
        table_data.append([
            Paragraph(row.category, styles["normal"]),
            row.start_time,
            row.end_time,
            f"{row.confidence:.3f}"
        ])

    col_widths = [70*mm, 35*mm, 35*mm, 30*mm]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)

    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "DejaVu"),
        ("FONTNAME", (0, 0), (-1, 0), "DejaVu-Bold"), # Жирный заголовок
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 1), (-1, -1), SOFT_RED), # Используем новый мягкий цвет
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
    ]))

    return table

# =======================
# СЕКЦИЯ
# =======================

def render_section(elements, section):
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(section["title"], styles["heading"]))

    # Красим текст статуса через inline-тег <font>
    if section["status"]: # Если есть ошибки (True)
        status_text = f'<font color="{TEXT_RED}">ПРОВАЛЕНО</font>'
    else:
        status_text = f'<font color="{TEXT_GREEN}">УСПЕШНО</font>'
        
    elements.append(Paragraph(f"<b>Статус:</b> {status_text}", styles["normal"]))

    elements.append(Spacer(1, 5))
    elements.append(build_status_table(section["status_table"]))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Обнаруженные проблемы", styles["subheading"]))
    elements.append(build_problems_table(section["problems_table"]))


def build_stats_chart(stats):
    if not stats:
        return None

    from matplotlib import font_manager
    import matplotlib.pyplot as plt
    import io

    # 1. Настройка шрифтов (проверьте правильность пути)
    font_path = "fonts/DejaVuSans.ttf"
    font_prop = font_manager.FontProperties(fname=font_path)
    
    categories = list(stats.keys())
    values = list(stats.values())

    # 2. Устанавливаем размер фигуры. 
    # Для ширины 160мм (~6.3 дюйма) ставим figsize=(8, 4) или (8, 5)
    fig, ax = plt.subplots(figsize=(8, 4.5)) 
    
    bars = ax.bar(categories, values, color='#FF9999', edgecolor='none', alpha=0.8)

    ax.set_title("Статистика обнаруженных нарушений по категориям", 
                 fontproperties=font_prop, fontsize=12, pad=20)
    ax.set_ylabel("Количество обнаружений", fontproperties=font_prop, fontsize=9)
    
    plt.xticks(fontproperties=font_prop, fontsize=8, rotation=45, ha='right')
    plt.yticks(fontsize=8)
    
    ax.yaxis.grid(True, linestyle='-', alpha=0.1)
    ax.set_axisbelow(True)
    
    # Убираем лишние рамки
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Подписи над барами
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                 f'{int(height)}', ha='center', va='bottom', 
                 fontproperties=font_prop, fontsize=8, fontweight='bold')

    # 3. Сохранение с ВЫСОКИМ DPI
    img_buffer = io.BytesIO()
    # tight_layout помогает избежать обрезки полей до сохранения
    plt.tight_layout()
    # Используем 300-600 DPI для типографского качества
    plt.savefig(img_buffer, format='png', dpi=400, bbox_inches='tight', transparent=True)
    img_buffer.seek(0)
    plt.close(fig)

    # 4. РАСЧЕТ РАЗМЕРОВ ДЛЯ REPORTLAB
    # Мы задаем ширину, а высоту вычисляем автоматически, чтобы не было искажений
    desired_width = 160 * mm
    # Получаем соотношение сторон из сохраненного изображения (опционально) или задаем константу
    # Чтобы график был "по ширине", используем hAlign='CENTER'
    img = Image(img_buffer)
    img.drawWidth = desired_width
    img.drawHeight = desired_width * 0.55  # Соотношение сторон примерно 16:9
    img.hAlign = 'CENTER'
    
    return img

# =======================
# ГЕНЕРАЦИЯ PDF
# =======================

def add_page_number(canvas, doc):
    page_num = canvas.getPageNumber()
    text = f"Страница {page_num}"
    
    canvas.setFont("DejaVu", 9)
    
    width, height = A4
    canvas.drawCentredString(width / 2, 10 * mm, text)


def generate_pdf(filename, sections, source_info=None, stats: dict[str, int]=None):
    doc = SimpleDocTemplate(
        filename, 
        pagesize=A4,
        leftMargin=15*mm,
        rightMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=15*mm
    )
    elements = []

    # --- ШАПКА ---
    elements.append(Paragraph("LINZA.Detector", styles["title"]))
    elements.append(Spacer(1, 5))
    elements.append(Paragraph("Структурированный отчет по видеофайлу", styles["centered"]))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("Общая информация:", styles["heading"]))

    # Данные
    elements.append(Paragraph(f"Источник: {source_info.video_path}", styles["normal"]))
    elements.append(Spacer(1, 5))
    elements.append(Paragraph(f"Длительность: {source_info.video_duration_formatted}", styles["normal"]))
    elements.append(Spacer(1, 5))
    elements.append(Paragraph(f"Дата анализа: {source_info.analysis_timestamp}", styles["normal"]))
    elements.append(Spacer(1, 5))
    elements.append(Paragraph(f"Время обработки: {source_info.processing_time_seconds} сек.", styles["normal"])) 
    elements.append(Spacer(1, 5))
    elements.append(Paragraph(f"Всего сцен: {source_info.frameCount}", styles["normal"]))
    # elements.append(Spacer(1, 5))
    # elements.append(Paragraph(f"Проблемных сцен: {source_info.fps}", styles["normal"]))

    elements.append(Spacer(1, 15))
    # --- РЕЗУЛЬТАТ ТЕСТА (Центрирование) ---
    global_status = any(section["status"] for section in sections)
    result_text = "ПРОВАЛЕНО" if global_status else "УСПЕШНО"
    
    # Создаем копию стиля heading и добавляем центрирование
    centered_heading = styles["heading"].clone('centered_heading')
    centered_heading.alignment = TA_CENTER
    
    elements.append(Paragraph(f"Результат теста: {result_text}", centered_heading))
    elements.append(Spacer(1, 15))

    # --- ГРАФИК И РАЗРЫВ СТРАНИЦЫ ---
    if stats:
        chart = build_stats_chart(stats)
        if chart:
            elements.append(chart)
            elements.append(Spacer(1, 15))
            # Добавляем разрыв страницы сразу после графика
            elements.append(PageBreak())
    
    # Линия разделения вместо PageBreak, если хотите визуально отделить шапку
    elements.append(Spacer(1, 5))

    # --- СЕКЦИИ ---
    for section in sections:
        render_section(elements, section)

    doc.build(
        elements,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number
    )
