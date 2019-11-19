from datetime import datetime, timedelta

import dateutil.parser
import isodate

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
            self.time_sleeping = self.wake_time - self.sleep_time
            self.interruptions = json_data['data'].get('interruptions')
            self.interruptions_text = ""
            if self.interruptions is not None:
                self.interruptions_text = self.format_interruptions()
        except KeyError:
            raise KeyError("Sleep data missing a wake or sleep time on {}".format(json_data['date']))

    def format_interruptions(self):
        return "{} interruption{} ({})".format(
            len(self.interruptions),
            "" if len(self.interruptions) == 1 else "s",
            ", ".join([self.format_interruption(x) for x in self.interruptions])
        )

    def format_interruption(self, interrupt):
        if "wake_time" and "sleep_time" in interrupt:
            start = dateutil.parser.parse(interrupt['wake_time'])
            end = dateutil.parser.parse(interrupt['sleep_time'])
            period = end-start
            return "{} minutes ({} - {})".format(int(period.total_seconds()//60), start.time(), end.time())
        elif "notes" in interrupt:
            return interrupt['notes']
        else:
            return "Unknown interruption"


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
        self.mood = {k: v for k, v in json_data['data'][time_str].items() if k != "message_id"}


class Chore:

    def __init__(self, json_data: DailysEntry):
        self.id = json_data['data']['id']
        self.display_name = json_data['data']['display_name']
        self.category = json_data['data']['category']
        self.recommended_period = isodate.parse_duration(json_data['data'].get("recommended_period"))
        self.latest_done = None

    def parse_date_entry(self, json_data: DailysEntry):
        date = json_data['date']
        chores_done = json_data['data']['chores_done']
        if self.id in chores_done:
            if self.latest_done is None or date > self.latest_done:
                self.latest_done = date

    def get_next_date(self):
        if self.recommended_period is None:
            return None
        if self.latest_done is None:
            return "Today"
        return self.latest_done + self.recommended_period
