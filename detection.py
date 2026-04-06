from typing import List

class Detection:
    """Детектированное событие"""
    
    startFrame: str
    endFrame: str
    subclass: str
    confidence: float
    e_type: str 

    def __init__(self, startframe, endframe, subclass, confidence, e_type):
        self.startFrame = format_time(startframe)
        self.endFrame = format_time(endframe)
        self.subclass = subclass
        self.confidence = confidence
        self.e_type = e_type
    def __repr__(self):
        return f"Detection(startFrame={self.startFrame}, endFrame={self.endFrame}, subclass={self.subclass}, confidence={self.confidence}, e_type={self.e_type})"


def format_time(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "{:02d}:{:02d}:{:02d}".format(h, m, s)


def get_by_subclasses(detections, subclass: List[str]) -> List[Detection]:
    """Возвращает список детектированных событий по категориям"""
    return [d for d in detections if d.subclass in subclass]

def get_count_by_subclasses(detections, subclass: List[str]) -> int:
    """Возвращает количество детектированных событий по категориям"""
    return len(get_by_subclasses(detections, subclass))

def read_from_json(detections_list):
    # Итерируемся по списку словарей и достаем значения по ключам
    result = [
        Detection(
            d["startFrame"], 
            d["endFrame"], 
            d["subclass"], 
            d["confidence"], 
            d["type"]
        ) for d in detections_list
    ]
    return result