from datetime import timedelta, datetime, date
from typing import Dict, List

import dateutil.parser

from dailys_models.models import Data
from dailys_models.sleep_data import SleepData


class MoodMeasurement(Data):
    """
    This is odd. It isn't actually dealing with an entire mood data entry.
    It is given the entire data entry, but only uses the part for the specified time
    TODO: Maybe pull this apart to be more normal.
    """
    def __init__(self, json_data, time_str, sleep_data):
        """
        :type json_data: dict
        :type time_str: str
        :type sleep_data: dict[date, models.sleep_data.SleepData]
        """
        super().__init__(json_data)
        if time_str == "WakeUpTime":
            self.datetime = sleep_data[self.date - timedelta(days=1)].wake_time
            self.time = self.datetime.time()
        elif time_str == "SleepTime":
            self.datetime = sleep_data[self.date].sleep_time
            self.time = self.datetime.time()
        else:
            self.time = dateutil.parser.parse(time_str).time()
            self.datetime = datetime.combine(self.date, self.time)
        self.mood = {k: v for k, v in json_data['data'][time_str].items() if k != "message_id"}

        
class MoodMeasurementEntry:
    def __init__(self, mood_date: date, time_str: str, mood_data: Dict) -> None:
        self.time_str = time_str
        self.time = time_str
        if time_str not in ["WakeUpTime", "SleepTime"]:
            self.time = dateutil.parser.parse(time_str).time()
        self.mood = {k: v for k, v in mood_data.items() if k != "message_id"}
    
    def value_count(self) -> int:
        return len(self.mood)
        
        
class MoodDay(Data):
    def __init__(self, json_data) -> None:
        super().__init__(json_data)
        self.measurements = {}
        for time_str, mood_data in self.raw_data["data"].items():
            self.measurements[time_str] = MoodMeasurementEntry(time_str, mood_data)
    
    def value_count(self) -> int:
        return sum(measurement.value_count() for measurement in self.measurements.values())
    
    def enhanced_measurements(self, all_sleep_entries: Dict[date, SleepData]) -> List[MoodMeasurement]:
        return [
            MoodMeasurement(self.raw_data, time_str, all_sleep_entries)
            for time_str in self.raw_data["data"].keys()
        ]
