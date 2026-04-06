import json


class SourceInfo:
    """Информация о источнике данных"""
    
    frameCount: int
    fps: float
    video_path: str
    video_duration_seconds: float
    processing_time_seconds: float
    processing_efficiency: float
    video_duration_formatted: str
    processing_time_formatted: str
    analysis_timestamp: str

    def __init__(self, frameCount, fps, video_path, video_duration_seconds, processing_time_seconds, processing_efficiency, video_duration_formatted, processing_time_formatted, analysis_timestamp):
        self.frameCount = frameCount
        self.fps = fps
        self.video_path = video_path
        self.video_duration_seconds = video_duration_seconds
        self.processing_time_seconds = processing_time_seconds
        self.processing_efficiency = processing_efficiency
        self.video_duration_formatted = video_duration_formatted
        self.processing_time_formatted = processing_time_formatted
        self.analysis_timestamp = analysis_timestamp


def read_from_json(data):
    """Читает информацию из json файла"""
    return SourceInfo(
        frameCount=data["frameCount"],
        fps=data["fps"],
        video_path=data["video_path"],
        video_duration_seconds=data["video_duration_seconds"],
        processing_time_seconds=data["processing_time_seconds"],
        processing_efficiency=data["processing_efficiency"],
        video_duration_formatted=data["video_duration_formatted"],
        processing_time_formatted=data["processing_time_formatted"],
        analysis_timestamp=data["analysis_timestamp"]
    )