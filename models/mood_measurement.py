from datetime import timedelta, datetime

import dateutil.parser

from models.models import Data


class MoodMeasurement(Data):
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
