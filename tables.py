class StatusTableRow:
    """Таблица статусов"""
    parameter: str
    status: str
    founded: str

    def __init__(self, parameter, status, founded):
        self.parameter = parameter
        self.status = status
        self.founded = founded

class ProblemsTableRow:
    """Таблица проблем"""
    category: str
    start_time: str
    end_time: str
    confidence: float

    def __init__(self, category, start_time, end_time, confidence):
        self.category = category
        self.start_time = start_time
        self.end_time = end_time
        self.confidence = confidence

    # def from_detection(self, detection):
    #     self.category = detection.subclass
    #     self.start_time = detection.startFrame
    #     self.end_time = detection.endFrame
    #     self.confidence = detection.confidence