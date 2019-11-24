from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional, Union

import dateutil.parser
import isodate
from colour_scale import ColourScale, format_colour

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

    def __init__(self, json_data: Dict[str, Any]):
        self.id = json_data['id']  # type: str
        self.display_name = json_data['display_name']  # type: str
        self.category = json_data['category']  # type: str
        self.recommended_period = None  # type: Optional[timedelta]
        if "recommended_period" in json_data and json_data['recommended_period'] is not None:
            self.recommended_period = isodate.parse_duration(json_data['recommended_period'])
        self.latest_done = None  # type: Optional[date]

    def parse_date_entry(self, json_data: DailysEntry):
        entry_date = json_data['date'].date()
        chores_done = json_data['data']['chores_done']
        if self.id in chores_done:
            if self.latest_done is None or entry_date > self.latest_done:
                self.latest_done = entry_date

    def get_next_date(self) -> Optional[Union[date, str]]:
        if self.recommended_period is None:
            return None
        if self.latest_done is None:
            return "Today"
        return self.latest_done + self.recommended_period

    def is_overdue(self) -> bool:
        if self.recommended_period is None:
            return False
        next_date = self.get_next_date()
        if next_date == "Today":
            return True
        today = date.today()
        return self.get_next_date() < today

    def get_latest_date_colour(self, colour_scale: ColourScale):
        if self.recommended_period is not None:
            return format_colour(colour_scale.null_colour)
        if self.latest_done is None:
            return format_colour(colour_scale.start_colour)
        return colour_scale.get_colour_for_value(self.latest_done)

    def get_next_date_colour(self, colour_scale: ColourScale):
        if self.is_overdue():
            return format_colour(colour_scale.start_colour)
        return format_colour(colour_scale.null_colour)

    def to_json(self):
        recommended_period = self.recommended_period
        if recommended_period is not None:
            recommended_period = isodate.duration_isoformat(recommended_period)
        latest_done = self.latest_done
        if isinstance(latest_done, date):
            latest_done = isodate.date_isoformat(latest_done)
        next_date = self.get_next_date()
        if isinstance(next_date, date):
            next_date = isodate.date_isoformat(next_date)
        return {
            "id": self.id,
            "display_name": self.display_name,
            "category": self.category,
            "recommended_period": recommended_period,
            "latest_done": latest_done,
            "next_date": next_date,
            "is_overdue": self.is_overdue(),
        }

    @staticmethod
    def from_complete_json(json_obj):
        chore = Chore(json_obj)
        if json_obj['latest_done'] is not None:
            chore.latest_done = isodate.parse_date(json_obj['latest_done'])
        return chore
