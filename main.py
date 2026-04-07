from typing import List

from parser import parse_json
from detection import get_by_subclasses, get_count_by_subclasses
from aliaces import CategoryAliases, DETECTION_NAMES_RU
from tables import ProblemsTableRow, StatusTableRow
import argparse

def generate_status_table(subclasses: List[str]):
    return [
    StatusTableRow(
        parameter=DETECTION_NAMES_RU[d],
        status="Провалено" if get_count_by_subclasses(result.detections, [d]) > 0 else "Успешно",
        founded="Не обнаружено" if get_count_by_subclasses(result.detections, [d]) == 0 else "Обнаружено"
        ) for d in subclasses
    ]

def generate_problems_table(subclasses: List[str]):
    return [
        ProblemsTableRow(
            category=DETECTION_NAMES_RU[d.subclass],
            start_time=d.startFrame,
            end_time=d.endFrame,
            confidence=d.confidence
        ) for d in get_by_subclasses(result.detections, subclasses)
    ]

parser = argparse.ArgumentParser(description="Generate report for LINZA.Detector")
parser.add_argument("input", type=str, help="Path to input file")
parser.add_argument("output", type=str, help="Path to output file")
args = parser.parse_args()

result = parse_json(args.input)

general_test_status = len(result.detections) > 0
drugs_subclasses = [CategoryAliases.DRUGS, CategoryAliases.DRUGS_KIDS, CategoryAliases.SMOKING, CategoryAliases.ALCOHOL]

drugs_group_total_status = get_count_by_subclasses(result.detections, drugs_subclasses) > 0
grugs_group_status_table = generate_status_table(drugs_subclasses)
drugs_group_problems_table = generate_problems_table(drugs_subclasses)


deviant_behavior_subclasses = [CategoryAliases.VIOLENCE, CategoryAliases.SUICIDE, CategoryAliases.TERROR, CategoryAliases.VANDALISM]
deviant_behavior_group_total_status = get_count_by_subclasses(result.detections, deviant_behavior_subclasses) > 0
deviant_behavior_group_status_table = generate_status_table(deviant_behavior_subclasses)
deviant_behavior_group_problems_table = generate_problems_table(deviant_behavior_subclasses)

nude_subclasses = [CategoryAliases.NUDE, CategoryAliases.SEX, CategoryAliases.LGBT]
nude_group_total_status = get_count_by_subclasses(result.detections, nude_subclasses) > 0
nude_group_status_table = generate_status_table(nude_subclasses)
nude_group_problems_table = generate_problems_table(nude_subclasses)

ludomania_subclasses = [CategoryAliases.LUDOMANIA]
ludomania_group_total_status = get_count_by_subclasses(result.detections, ludomania_subclasses) > 0
ludomania_group_status_table = generate_status_table(ludomania_subclasses)
ludomania_group_problems_table = generate_problems_table(ludomania_subclasses)

extremism_subclasses = [CategoryAliases.EXTREMISM, CategoryAliases.ANTIPATRIOTIC, CategoryAliases.INOAGENTS, CategoryAliases.INOAGENT_CONTENT]
extremism_group_total_status = get_count_by_subclasses(result.detections, extremism_subclasses) > 0
extremism_group_status_table = generate_status_table(extremism_subclasses)
extremism_group_problems_table = generate_problems_table(extremism_subclasses)

from pdf_report import generate_pdf

sections = [
    {
        "title": "Наркотические вещества, курение, инъекции",
        "status": drugs_group_total_status,
        "status_table": grugs_group_status_table,
        "problems_table": drugs_group_problems_table
    },
    {
        "title": "Девиантное и асоциальное поведение",
        "status": deviant_behavior_group_total_status,
        "status_table": deviant_behavior_group_status_table,
        "problems_table": deviant_behavior_group_problems_table
    },
    {
        "title": "Тотализаторы, букмейкеры и казино (лудомания)",
        "status": ludomania_group_total_status,
        "status_table": ludomania_group_status_table,
        "problems_table": ludomania_group_problems_table
    },
    {
        "title": "Терроризм, нацизм и экстремизм",
        "status": extremism_group_total_status,
        "status_table": extremism_group_status_table,
        "problems_table": extremism_group_problems_table
    },
    {
        "title": "Эротика, порно",
        "status": nude_group_total_status,
        "status_table": nude_group_status_table,
        "problems_table": nude_group_problems_table
    }
]

report_stats = {
    "Наркотические вещества...": get_count_by_subclasses(result.detections, drugs_subclasses),
    "Девиантное и асоциальное ...": get_count_by_subclasses(result.detections, deviant_behavior_subclasses),
    "Тотализаторы, букмейкеры...": get_count_by_subclasses(result.detections, ludomania_subclasses),
    "Экстремизм....": get_count_by_subclasses(result.detections, extremism_subclasses),
    "Эротика, порно": get_count_by_subclasses(result.detections, nude_subclasses)
}

generate_pdf(args.output, sections, result.source_info, report_stats)
