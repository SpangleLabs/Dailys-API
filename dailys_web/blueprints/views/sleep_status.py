import re
from datetime import datetime, timezone
from typing import Any

import flask
import pytz

from dailys_models.sleep_data import SleepData
from dailys_web.blueprints.views.base_view import View


def timedelta_to_iso8601_duration(delta):
    days = delta.days
    total_seconds = delta.seconds
    hours = total_seconds // 3600
    total_seconds -= hours * 3600
    minutes = total_seconds // 60
    total_seconds -= minutes * 60
    seconds = total_seconds
    return "P{}DT{}H{}M{}S".format(days, hours, minutes, seconds)


def format_duration(iso_duration):
    days, hours, minutes, seconds = 0, 0, 0, 0
    search_days = re.search(r"([0-9]+)D", iso_duration)
    if search_days:
        days = search_days.group(1)
    search_hours = re.search(r"T.*?([0-9]+)H", iso_duration)
    if search_hours:
        hours = search_hours.group(1)
    search_minutes = re.search(r"T.*?([0-9]+)M", iso_duration)
    if search_minutes:
        minutes = search_minutes.group(1)
    search_seconds = re.search(r"T.*?([0-9]+)S", iso_duration)
    if search_seconds:
        seconds = search_seconds.group(1)
    return f"{days} days, {hours} hours, {minutes} minutes, and {seconds} seconds"


class SleepStatusJsonView(View):

    def __init__(self, data_source, config):
        super().__init__(data_source)
        self.config = config

    def get_path(self):
        return "/sleep_status.json"

    def call(self, **kwargs):
        raw_sleeps = self.data_source.get_latest_n_entries_for_stat("sleep", 2)
        sleeps = [SleepData.from_entry(e) for e in raw_sleeps]
        # Figure out whether they are sleeping
        latest_wake_time = sleeps[0].wake_time
        is_sleeping = latest_wake_time is not None
        response: dict[str, Any] = {
            "is_sleeping": is_sleeping
        }
        # Figure out the local timezone to display
        now_zone = timezone.utc
        if "timezone" in self.config:
            now_zone = pytz.timezone(self.config["timezone"])
        time_now = datetime.now(now_zone)
        # If they're awake, add awake data
        if latest_wake_time is not None:
            wake_time = latest_wake_time
            sleep_time = sleeps[0].sleep_time
            response["awake_start"] = wake_time
            response["time_asleep"] = timedelta_to_iso8601_duration(wake_time - sleep_time)
            response["time_awake"] = timedelta_to_iso8601_duration(time_now - wake_time)
        else:
            wake_time = sleeps[1].wake_time
            if wake_time is None:
                raise ValueError("You haven't woken up today, but you didn't wake up yesterday either?")
            sleep_time = sleeps[0].sleep_time
            response["sleep_start"] = sleep_time
            response["time_asleep"] = timedelta_to_iso8601_duration(time_now - sleep_time)
            response["time_awake"] = timedelta_to_iso8601_duration(sleep_time - wake_time)
        return flask.jsonify(response)


class SleepStatusView(SleepStatusJsonView):

    def get_path(self):
        return "/sleep_status/"

    def call(self, **kwargs):
        status = super().call().get_json()
        return flask.render_template("sleep_status.html", status=status, format=format_duration)
