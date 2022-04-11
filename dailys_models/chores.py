from datetime import date
from typing import Dict, Any, Optional, Union

import isodate

from dailys_web.colour_scale import ColourScale, format_colour
from dailys_web.data_source import DailysEntry


class Chore:
    """
    Doesn't extend Data as this is not a model of a full data entry, just a single chore entry in a chores/static entry
    """

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
        today = date.today()
        next_date = self.latest_done + self.recommended_period
        if today == next_date:
            return "Today"
        return next_date

    def is_overdue(self) -> bool:
        if self.recommended_period is None:
            return False
        next_date = self.get_next_date()
        if next_date == "Today":
            return True
        today = date.today()
        return self.get_next_date() <= today

    def days_overdue(self) -> Optional[int]:
        if self.recommended_period is None:
            return None
        next_date = self.get_next_date()
        if next_date == "Today":
            return 0
        today = date.today()
        return (today - self.get_next_date()).days

    def days_since_done(self) -> Optional[int]:
        if self.latest_done is None:
            return None
        today = date.today()
        return (today - self.latest_done).days

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
