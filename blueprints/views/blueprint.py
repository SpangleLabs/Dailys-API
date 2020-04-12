import json
import math
import re
from typing import Dict

import dateutil
import flask
from datetime import timedelta, timezone, datetime, date, time

import isodate
import numpy
import pytz
from dateutil.relativedelta import relativedelta

from blueprints.views.sleep_time import SleepTimeRangeView, SleepTimeView
from colour_scale import ColourScale
from data_source import DataSource
from decorators import view_auth_required
from models import SleepData, FuraffinityData, MoodMeasurement, Chore, DreamNight
from blueprints.base_blueprint import BaseBlueprint


class ViewsBlueprint(BaseBlueprint):

    def __init__(self, data_source: DataSource, config: Dict[str, str]):
        super().__init__(data_source, "views")
        self.config = config

    def _list_views(self):
        return [
            SleepTimeRangeView(self.data_source),
            SleepTimeView(self.data_source)
        ]

    def register(self):
        self.blueprint.route("/")(self.list_views)
        for view in self._list_views():
            self.blueprint.add_url_rule(view.get_path(), f"{view.__class__.__name__}_call", view.call)
        self.blueprint.route("/fa_notifications/<start_date:start_date>/<end_date:end_date>")(self.view_fa_notifications_range)
        self.blueprint.route("/fa_notifications/")(self.view_fa_notification_stats)
        self.blueprint.route("/mood/<start_date:start_date>/<end_date:end_date>")(self.view_mood_stats_range)
        self.blueprint.route("/mood/")(self.view_mood_stats)
        self.blueprint.route("/mood_weekly/<start_date:start_date>/<end_date:end_date>")(self.view_mood_weekly_range)
        self.blueprint.route("/mood_weekly/")(self.view_mood_weekly_stats)
        self.blueprint.route("/stats/<start_date:start_date>/<end_date:end_date>")(self.view_stats_over_range)
        self.blueprint.route("/stats/")(self.view_stats)
        self.blueprint.route("/sleep_status.json")(self.view_sleep_status_json)
        self.blueprint.route("/sleep_status/")(self.view_sleep_status)
        self.blueprint.route("/named_dates/")(self.view_named_dates)
        self.blueprint.route("/chores_board.json")(self.view_chores_board_json)
        self.blueprint.route("/chores_board/")(self.view_chores_board)
        self.blueprint.route("/dreams/<start_date:start_date>/<end_date:end_date>")(self.view_dreams_over_range)
        self.blueprint.route("/dreams/")(self.view_dreams)

    @view_auth_required
    def list_views(self):
        views = [
            "sleep_time", "fa_notifications", "mood", "mood_weekly", "stats", "sleep_status", "sleep_status.json",
            "named_dates", "chores_board.json", "chores_board", "dreams"
        ]
        return flask.render_template("list_views.html", views=views)

    @view_auth_required
    def view_fa_notifications_range(self, start_date, end_date):
        # Get data
        fa_data_response = self.data_source.get_entries_for_stat_over_range("furaffinity", start_date, end_date)
        fa_data = {
            FuraffinityData(x).date: {"data": FuraffinityData(x)}
            for x in fa_data_response
        }
        # Add in diff data
        for today in fa_data.keys():
            yesterday = today - timedelta(days=1)
            fa_data[today]['diff'] = None
            if yesterday in fa_data:
                diff = fa_data[today]['data'].total - fa_data[yesterday]['data'].total
                if diff >= 0:
                    fa_data[today]['diff'] = diff
        # Create colour scale
        max_notif = max([x['data'].total for x in fa_data.values()])
        scale = ColourScale(0, max_notif, ColourScale.WHITE, ColourScale.RED)
        # Render template
        return flask.render_template("fa_notifications.html", fa_notifications=fa_data, scale=scale)

    @view_auth_required
    def view_fa_notification_stats(self):
        return self.view_fa_notifications_range("earliest", "latest")

    @view_auth_required
    def view_mood_stats_range(self, start_date, end_date):
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
        # Create scales
        scale = ColourScale(1, 5, ColourScale.WHITE, ColourScale.DANDELION)
        # TODO: define what mood measurements are good vs bad
        scale_good = ColourScale(1, 5, ColourScale.WHITE, ColourScale.GREEN)
        scale_bad = ColourScale(1, 5, ColourScale.WHITE, ColourScale.RED)
        # Render template
        return flask.render_template(
            "mood.html",
            mood_static=mood_static,
            mood_measurements=mood_measurements,
            scale=scale,
            scale_good=scale_good,
            scale_bad=scale_bad
        )

    @view_auth_required
    def view_mood_stats(self):
        return self.view_mood_stats_range("earliest", "latest")

    @view_auth_required
    def view_mood_weekly_range(self, start_date, end_date):
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
            mood_static=mood_static,
            weekdays=weekdays,
            weekday_mood_scales=weekday_mood_scales,
            weekly_mood_scales=weekly_mood_scales,
            weekday_stats=weekday_stats,
            weekly_stats=weekly_stats
        )

    @view_auth_required
    def view_mood_weekly_stats(self):
        return self.view_mood_weekly_range("earliest", "latest")

    @view_auth_required
    def view_stats_over_range(self, start_date, end_date):
        stat_list = self.data_source.get_entries_over_range(start_date, end_date)
        # Calculations for stats -> values
        value_calc = {
            "sleep": lambda x: 3,
            "mood": lambda x: len(x.keys()) * len([y for y in x[list(x)[0]].keys() if y != "message_id"]),
            "duolingo": lambda x: len(x.keys()),
            "furaffinity": lambda x: 7 if "total" in x else 1,
            "chores": lambda x: len(x['chores_done']),
            "dreams": lambda x: len(x["dreams"]) + len([y for y in x.keys() if y not in ["dreams"] and x[y]])
        }
        # Calculate date and source totals
        date_totals = {}
        source_totals = {}
        stat_totals = {}
        for stat in stat_list:
            stat_name = stat["stat_name"]
            stat_date = stat["date"].date()
            source = stat["source"]
            values_count = value_calc.get(stat_name, lambda x: 0)(stat["data"])
            # Update date totals
            if stat_date not in date_totals:
                date_totals[stat_date] = {"stats": 0, "values": 0}
            date_totals[stat_date]['stats'] += 1
            date_totals[stat_date]['values'] += values_count
            # Update source totals
            if source not in source_totals:
                source_totals[source] = {"stats": 0, "values": 0}
            source_totals[source]["stats"] += 1
            source_totals[source]["values"] += values_count
            # Update stat totals
            if stat_name not in stat_totals:
                stat_totals[stat_name] = {"stats": 0, "values": 0}
            stat_totals[stat_name]["stats"] += 1
            stat_totals[stat_name]["values"] += values_count
        # Sum up totals
        total_stats = sum([source_totals[x]['stats'] for x in source_totals.keys()])
        total_values = sum([source_totals[x]['values'] for x in source_totals.keys()])

        return flask.render_template(
            "total_stats.html",
            total_stats=total_stats,
            total_values=total_values,
            date_totals=date_totals,
            source_totals=source_totals,
            stat_totals=stat_totals
        )

    @view_auth_required
    def view_stats(self):
        return self.view_stats_over_range("earliest", "latest")

    @view_auth_required
    def view_sleep_status_json(self):
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
            wake_time = now_zone.localize(dateutil.parser.parse(sleeps[0]["wake_time"]))
            sleep_time = now_zone.localize(dateutil.parser.parse(sleeps[0]["sleep_time"]))
            response["awake_start"] = sleeps[0]["wake_time"]
            response["time_asleep"] = timedelta_to_iso8601_duration(wake_time - sleep_time)
            response["time_awake"] = timedelta_to_iso8601_duration(time_now - wake_time)
        else:
            wake_time = now_zone.localize(dateutil.parser.parse(sleeps[1]["wake_time"]))
            sleep_time = now_zone.localize(dateutil.parser.parse(sleeps[0]["sleep_time"]))
            response["sleep_start"] = sleeps[0]["sleep_time"]
            response["time_asleep"] = timedelta_to_iso8601_duration(time_now - sleep_time)
            response["time_awake"] = timedelta_to_iso8601_duration(sleep_time - wake_time)
        return flask.jsonify(response)

    @view_auth_required
    def view_sleep_status(self):
        status = self.view_sleep_status_json().get_json()
        return flask.render_template("sleep_status.html", status=status, format=format_duration)

    @view_auth_required
    def view_named_dates(self):
        with open("named-dates.json", "r") as f:
            data = json.load(f)
            named_dates = {k: datetime.strptime(v, '%Y-%m-%d').date() for k, v in data.items()}
        return flask.render_template("named_dates.html", dates=named_dates)

    @view_auth_required
    def view_chores_board_json(self):
        today = date.today()
        chores_static = self.data_source.get_entries_for_stat_on_date("chores", "static")[0]
        chores_data = self.data_source.get_entries_for_stat_over_range("chores", "earliest", "latest")
        chores = [Chore(x) for x in chores_static['data']['chores']]
        for chore_date in chores_data:
            for chore in chores:
                chore.parse_date_entry(chore_date)
        # Sort chores into categories
        categorised_chores = dict()
        for chore in chores:
            if chore.category not in categorised_chores:
                categorised_chores[chore.category] = []
            categorised_chores[chore.category].append(chore)
        # Get layout info
        layout = chores_static['data']['layout']
        # Return json
        return flask.jsonify({
            "today": isodate.date_isoformat(today),
            "chores": {k: [x.to_json() for x in v] for k, v in categorised_chores.items()},
            "layout": layout
        })

    @view_auth_required
    def view_chores_board(self):
        chores_board = self.view_chores_board_json().get_json()
        today = isodate.parse_date(chores_board['today'])
        categorised_chores = {k: [Chore.from_complete_json(x) for x in v] for k, v in chores_board['chores'].items()}
        layout = chores_board['layout']
        # Calculate overdue and neglected chores
        overdue_chores = []
        neglected_chores = []
        for chore_list in categorised_chores.values():
            for chore in chore_list:
                if chore.recommended_period is not None:
                    if chore.is_overdue():
                        overdue_chores.append(chore)
                else:
                    neglected_chores.append(chore)
        # Sort overdue and neglected chores lists
        overdue_chores.sort(key=lambda x: x.days_overdue(), reverse=True)
        neglected_chores.sort(key=lambda x: x.days_since_done() or math.inf, reverse=True)
        # Colour scales for non-recommended-period chores
        start_colouring = today - isodate.parse_duration("P2M")
        end_colouring = today - isodate.parse_duration("P1W")
        colour_scale = ColourScale(
            start_colouring, end_colouring,
            ColourScale.RED, ColourScale.WHITE
        )
        # Render
        return flask.render_template(
            "chores_board.html",
            today=today,
            categorised_chores=categorised_chores,
            layout=layout,
            overdue_chores=overdue_chores,
            neglected_chores=neglected_chores,
            colour_scale=colour_scale,
        )

    @view_auth_required
    def view_dreams_over_range(self, start_date, end_date):
        dreams_data = self.data_source.get_entries_for_stat_over_range("dreams", start_date, end_date)
        dream_nights = [DreamNight(x) for x in dreams_data]
        static_data = self.data_source.get_entries_for_stat_on_date("dreams", "static")
        # Fill in missing dates
        if static_data and "all_nights_start" in static_data[0]["data"]:
            dream_dates = [night.date.date() for night in dream_nights]
            start_date = dateutil.parser.parse(static_data[0]["data"]["all_nights_start"]).date()
            end_date = max(dream_dates)
            current_date = max(start_date, min(dream_dates))
            while current_date <= end_date:
                if current_date not in dream_dates:
                    dream_nights.append(DreamNight({"date": datetime.combine(current_date, time(0, 0, 0)), "source": "Auto-generated", "stat_name": "dreams", "data": {"dreams": []}}))
                current_date += relativedelta(days=1)
            dream_nights.sort(key=lambda x: x.date.date())
        # Stats
        count_with_dreams = len([night for night in dream_nights if night.dream_count > 0])
        count_without_dreams = len(dream_nights) - count_with_dreams
        percentage_with_dreams = f"{100*(count_with_dreams / len(dream_nights)):.2f}%"
        max_dreams = max([night.dream_count for night in dream_nights])
        max_length = max([night.total_dreams_length for night in dream_nights])
        # Scales
        dream_count_scale = ColourScale(
            0, max(len(night.dreams) for night in dream_nights),
            ColourScale.WHITE, ColourScale.RED
        )
        dream_length_scale = ColourScale(
            0, max(night.total_dreams_length for night in dream_nights),
            ColourScale.WHITE, ColourScale.RED
        )
        return flask.render_template(
            "dreams.html",
            dream_nights=dream_nights,
            count_with_dreams=count_with_dreams,
            count_without_dreams=count_without_dreams,
            percentage_with_dreams=percentage_with_dreams,
            max_dreams=max_dreams,
            max_length=max_length,
            dream_count_scale=dream_count_scale,
            dream_length_scale=dream_length_scale
        )

    @view_auth_required
    def view_dreams(self):
        return self.view_dreams_over_range("earliest", "latest")


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

