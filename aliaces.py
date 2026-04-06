DETECTION_NAMES_RU = {
    "alcohol": "Демонстрация алкоголя",
    "smoking": "Демонстрация курения",
    "drugs": "Наркотические вещества",
    "drugs_kids": "Побуждающая детей к запрещённым веществам либо к вещам 18+",
    "terror": "Терроризм",
    "vandalism": "Воровство, разбой, вандализм",
    "violence": "Призывы к насилию",
    "suicide": "Побуждающая детей к самоубийству либо причинению вреда своему здоровью",
    "nude": "Информация эротического характера",
    "sex": "Информация порнографического характера",
    "lgbt": "Пропаганда ЛГБТ",
    "ludomania": "Демонстрация рекламы относящийся к казино и подобного рода рекламы",
    "extremism": "Экстремизм, нацизм",
    "antipatriotic": "Антипатриотический контент",
    "inoagents": "Иноагенты",
    "inoagentcontent": "Продукция произведенная иностранными агентами"
}

# Обратный словарь (по описанию)
DETECTION_CODES_BY_NAME = {v: k for k, v in DETECTION_NAMES_RU.items()}


class CategoryAliases:
    """Класс с алиасами для быстрого доступа к кодам категорий"""
    ALCOHOL = "alcohol"
    SMOKING = "smoking"
    DRUGS = "drugs"
    DRUGS_KIDS = "drugs_kids"
    TERROR = "terror"
    VANDALISM = "vandalism"
    VIOLENCE = "violence"
    SUICIDE = "suicide"
    NUDE = "nude"
    SEX = "sex"
    LGBT = "lgbt"
    LUDOMANIA = "ludomania"
    EXTREMISM = "extremism"
    ANTIPATRIOTIC = "antipatriotic"
    INOAGENTS = "inoagents"
    INOAGENT_CONTENT = "inoagentcontent"

