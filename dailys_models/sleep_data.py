import abc
import datetime
from typing import Optional

import dateutil.parser

from dailys_models.models import Data

class CurrentlySleeping(Exception):
    pass


class SleepData(Data, abc.ABC):

    @classmethod
    def from_entry(cls, json_data: dict) -> "SleepData":
        try:
            return FullSleepData(json_data)
        except CurrentlySleeping:
            return PartialSleepData(json_data)
    
    @property
    @abc.abstractmethod
    def is_sleeping(self) -> bool:
        raise NotImplemented

    @property
    @abc.abstractmethod
    def sleep_time(self) -> datetime.datetime:
        raise NotImplemented

    @property
    @abc.abstractmethod
    def wake_time(self) -> Optional[datetime.datetime]:
        raise NotImplemented


class PartialSleepData(SleepData):
    @property
    def is_sleeping(self) -> bool:
        return "wake_time" in self.raw_data["data"]

    @property
    def wake_time(self) -> Optional[datetime.datetime]:
        return None

    @property
    def sleep_time(self) -> datetime.datetime:
        return dateutil.parser.parse(self.raw_data["data"]["sleep_time"])


class FullSleepData(SleepData):
    def __init__(self, json_data: dict) -> None:
        super().__init__(json_data)
        self.time_sleeping = self.wake_time - self.sleep_time
        self.interruptions = json_data['data'].get('interruptions')
        self.interruptions_text = ""
        if self.interruptions is not None:
            self.interruptions_text = self.format_interruptions()

    @property
    def is_sleeping(self) -> bool:
        return False

    @property
    def wake_time(self) -> Optional[datetime.datetime]:
        try:
            return dateutil.parser.parse(self.raw_data["data"]["wake_time"])
        except KeyError:
            raise CurrentlySleeping("Sleep data indicates that you are currently sleeping, on {}".format(self.date))

    @property
    def sleep_time(self) -> datetime.datetime:
        try:
            return dateutil.parser.parse(self.raw_data["data"]["sleep_time"])
        except KeyError:
            raise KeyError("Sleep data missing a sleep time on {}".format(self.date))

    def format_interruptions(self) -> str:
        return "{} interruption{} ({})".format(
            len(self.interruptions),
            "" if len(self.interruptions) == 1 else "s",
            ", ".join([self.format_interruption(x) for x in self.interruptions])
        )

    def format_interruption(self, interrupt: dict) -> str:
        if "wake_time" and "sleep_time" in interrupt:
            start = dateutil.parser.parse(interrupt['wake_time'])
            end = dateutil.parser.parse(interrupt['sleep_time'])
            period = end - start
            return "{} minutes ({} - {})".format(int(period.total_seconds() // 60), start.time(), end.time())
        elif "notes" in interrupt:
            return interrupt['notes']
        else:
            return "Unknown interruption"
    
    def format_sleep_time(self, timezone):
        return self.sleep_time.astimezone(timezone).strftime("%H:%M:%S")

    def format_wake_time(self, timezone):
        return self.wake_time.astimezone(timezone).strftime("%H:%M:%S")
    
    def format_time_sleeping(self) -> str:
        hours, seconds = divmod(self.time_sleeping.total_seconds(), 3600)
        minutes, seconds = divmod(seconds, 60)
        return f"{hours:.0f}h {minutes:.0f}m {seconds:.0f}s"
    
    def value_count(self) -> int:
        return sum(int(bool(x)) for x in [self.sleep_time, self.wake_time, self.interruptions])
