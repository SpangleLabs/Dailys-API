from datetime import datetime, timedelta

import dateutil.parser

from data_source import DailysEntry


class Data:

    def __init__(self, json_data: DailysEntry):
        self.date = json_data['date']
        self.source = json_data['source']
        self.stat_name = json_data['stat_name']


class SleepData(Data):

    def __init__(self, json_data):
        super().__init__(json_data)
        try:
            self.sleep_time = dateutil.parser.parse(json_data['data']['sleep_time'])
            self.wake_time = dateutil.parser.parse(json_data['data']['wake_time'])
        except KeyError:
            raise KeyError("Missing sleep or wake time for date {}".format(json_data['date']))
        self.time_sleeping = self.wake_time - self.sleep_time
        self.interruptions = json_data['data'].get('interruptions')


class FuraffinityData(Data):

    def __init__(self, json_data):
        super().__init__(json_data)
        self.submissions = json_data['data'].get('submissions')
        self.comments = json_data['data'].get('comments')
        self.journals = json_data['data'].get('journals')
        self.notes = json_data['data'].get('notes')
        self.watches = json_data['data'].get('watches')
        self.favourites = json_data['data'].get('favourites')
        self.total = json_data['data'].get(
            "total",
            sum(filter(None,
                       [self.submissions, self.comments, self.journals, self.notes, self.watches, self.favourites]))
        )


class MoodMeasurement(Data):
    def __init__(self, json_data, time_str, sleep_data):
        """
        :type json_data: dict
        :type time_str: str
        :type sleep_data: dict[date, SleepData]
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
        self.mood = {k: v for k,v in json_data['data'][time_str].items() if k != "message_id"}

