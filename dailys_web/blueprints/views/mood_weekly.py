from datetime import timedelta

import flask
import numpy

from dailys_web.blueprints.views.base_view import View
from dailys_web.colour_scale import ColourScale
from dailys_models.mood_measurement import MoodMeasurement
from dailys_models.sleep_data import SleepData
from dailys_web.nav_data import NavData


class MoodWeeklyRangeView(View):
    def get_path(self):
        return "/mood_weekly/<start_date:start_date>/<end_date:end_date>/"

    def call(self, **kwargs):
        start_date = kwargs["start_date"]
        end_date = kwargs["end_date"]
        # Get static mood data
        mood_static = self.data_source.get_entries_for_stat_on_date("mood", "static")[0]['data']
        # Get mood data
        mood_data = self.data_source.get_entries_for_stat_over_range("mood", start_date, end_date)
        # Get sleep data, if necessary
        sleep_data = {}
        if "WakeUpTime" in mood_static['times'] or "SleepTime" in mood_static['times']:
            sleep_start_date = start_date
            if start_date != "earliest":
                sleep_start_date -= timedelta(days=1)
            sleep_end_date = end_date
            if end_date != "latest":
                sleep_end_date -= timedelta(days=1)
            sleep_data_response = self.data_source.get_entries_for_stat_over_range("sleep", sleep_start_date, sleep_end_date)
            sleep_data = {SleepData(x).date: SleepData(x) for x in sleep_data_response}
        # Create list of mood measurements
        mood_measurements = [
            MoodMeasurement(x, mood_time, sleep_data)
            for x in mood_data
            for mood_time in mood_static['times']
            if mood_time in x['data']
        ]
        # Generate week day stats
        weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekday_stats = {
            day: {
                mood: {"list": []}
                for mood in mood_static['moods']
            }
            for day in weekdays
        }
        for measurement in mood_measurements:
            for mood, val in measurement.mood.items():
                if mood not in mood_static['moods']:
                    continue
                weekday_stats[measurement.date.strftime("%A")][mood]["list"].append(int(val))
        for day in weekday_stats.keys():
            for mood in weekday_stats[day].keys():
                weekday_stats[day][mood]["avg"] = numpy.mean(weekday_stats[day][mood]["list"])
        # Generate weekly table
        weekly_stats = {}
        for measurement in mood_measurements:
            week = measurement.date.strftime("%G-%V")
            if week not in weekly_stats:
                weekly_stats[week] = {}
                for mood in mood_static['moods']:
                    weekly_stats[week][mood] = {"list": []}
            for mood, val in measurement.mood.items():
                weekly_stats[week][mood]['list'].append(int(val))
        for week in weekly_stats:
            for mood in weekly_stats[week]:
                weekly_stats[week][mood]['avg'] = numpy.mean(weekly_stats[week][mood]['list'])
        # Create scales
        weekday_mood_scales = {
            mood: ColourScale(
                min([
                    weekday_stats[day][mood]["avg"]
                    for day in weekdays
                    if not numpy.isnan(weekday_stats[day][mood]["avg"])
                ]),
                max([
                    weekday_stats[day][mood]["avg"]
                    for day in weekdays
                    if not numpy.isnan(weekday_stats[day][mood]["avg"])
                ]),
                ColourScale.WHITE,
                ColourScale.DANDELION
            )
            for mood in mood_static['moods']
        }
        weekly_mood_scales = {
            mood: ColourScale(
                min(
                    [
                        weekly_stats[week][mood]["avg"]
                        for week in weekly_stats.keys()
                        if not numpy.isnan(weekly_stats[week][mood]["avg"])
                    ]
                ),
                max(
                    [
                        weekly_stats[week][mood]["avg"]
                        for week in weekly_stats.keys()
                        if not numpy.isnan(weekly_stats[week][mood]["avg"])
                    ]
                ),
                ColourScale.WHITE,
                ColourScale.DANDELION
            )
            for mood in mood_static['moods']
        }
        # Render page
        return flask.render_template(
            "mood_weekly.html",
            nav_data=NavData(),
            mood_static=mood_static,
            weekdays=weekdays,
            weekday_mood_scales=weekday_mood_scales,
            weekly_mood_scales=weekly_mood_scales,
            weekday_stats=weekday_stats,
            weekly_stats=weekly_stats
        )


class MoodWeeklyView(MoodWeeklyRangeView):

    def get_path(self):
        return "/mood_weekly/"

    def call(self, **kwargs):
        return super().call(start_date="earliest", end_date="latest")
