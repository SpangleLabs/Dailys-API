import re
from datetime import datetime, timezone

import dateutil.parser
import flask
import pytz

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
        sleeps = self.data_source.get_latest_n_entries_for_stat("sleep", 2)
        is_awake = "wake_time" in sleeps[0]
        response = {
            "is_sleeping": not is_awake
        }
        now_zone = timezone.utc
        if "timezone" in self.config:
            now_zone = pytz.timezone(self.config["timezone"])
        time_now = datetime.now(now_zone)
        if is_awake:
            wake_time = dateutil.parser.parse(sleeps[0]["wake_time"])
            sleep_time = dateutil.parser.parse(sleeps[0]["sleep_time"])
            response["awake_start"] = sleeps[0]["wake_time"]
            response["time_asleep"] = timedelta_to_iso8601_duration(wake_time - sleep_time)
            response["time_awake"] = timedelta_to_iso8601_duration(time_now - wake_time)
        else:
            wake_time = dateutil.parser.parse(sleeps[1]["wake_time"])
            sleep_time = dateutil.parser.parse(sleeps[0]["sleep_time"])
            response["sleep_start"] = sleeps[0]["sleep_time"]
            response["time_asleep"] = timedelta_to_iso8601_duration(time_now - sleep_time)
            response["time_awake"] = timedelta_to_iso8601_duration(sleep_time - wake_time)
        return flask.jsonify(response)


class SleepStatusView(SleepStatusJsonView):

    def get_path(self):
        return "/sleep_status/"

    def call(self, **kwargs):
        status = super().call().get_json()
        return flask.render_template("sleep_status.html", status=status, format=format_duration)
