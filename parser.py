import json
from typing import List 
from source_info import SourceInfo, read_from_json as read_source_info
from detection import Detection, read_from_json as read_detections

class ParsingResult:
    """Результат разбора данных"""
    
    source_info: SourceInfo
    detections: List[Detection]

    def __init__(self, source_info, detections):
        self.source_info = source_info
        self.detections = detections

def parse_json(file_path: str) -> ParsingResult:
    with open(file_path, "r") as f:
        data = json.load(f)
        source_info = read_source_info(data["sourceInfo"])
        detections = read_detections(data["detections"])
        result = ParsingResult(source_info, detections)
        return result



    

    