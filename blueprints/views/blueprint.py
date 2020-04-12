import json
import math
from typing import Dict

import dateutil
import flask
from datetime import datetime, date, time

import isodate
from dateutil.relativedelta import relativedelta

from blueprints.views.fa_notifications import FANotificationsRangeView, FANotificationsView
from blueprints.views.mood import MoodRangeView, MoodView
from blueprints.views.mood_weekly import MoodWeeklyRangeView, MoodWeeklyView
from blueprints.views.sleep_status import SleepStatusJsonView, SleepStatusView
from blueprints.views.sleep_time import SleepTimeRangeView, SleepTimeView
from colour_scale import ColourScale
from data_source import DataSource
from decorators import view_auth_required
from models import Chore, DreamNight
from blueprints.base_blueprint import BaseBlueprint


class ViewsBlueprint(BaseBlueprint):

    def __init__(self, data_source: DataSource, config: Dict[str, str]):
        super().__init__(data_source, "views")
        self.config = config

    def _list_views(self):
        return [
            SleepTimeRangeView(self.data_source),
            SleepTimeView(self.data_source),
            FANotificationsRangeView(self.data_source),
            FANotificationsView(self.data_source),
            MoodRangeView(self.data_source),
            MoodView(self.data_source),
            MoodWeeklyRangeView(self.data_source),
            MoodWeeklyView(self.data_source),
            SleepStatusJsonView(self.data_source, self.config),
            SleepStatusView(self.data_source, self.config)
        ]

    def register(self):
        self.blueprint.route("/")(self.list_views)
        for view in self._list_views():
            self.blueprint.add_url_rule(view.get_path(), f"{view.__class__.__name__}_call", view.call)
        self.blueprint.route("/named_dates/")(self.view_named_dates)
        self.blueprint.route("/chores_board.json")(self.view_chores_board_json)
        self.blueprint.route("/chores_board/")(self.view_chores_board)
        self.blueprint.route("/dreams/<start_date:start_date>/<end_date:end_date>")(self.view_dreams_over_range)
        self.blueprint.route("/dreams/")(self.view_dreams)

    @view_auth_required
    def list_views(self):
        views = [view.get_path() for view in self._list_views() if "<" not in view.get_path()]
        return flask.render_template("list_views.html", views=views)

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


