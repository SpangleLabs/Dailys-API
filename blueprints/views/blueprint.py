import json
from typing import Dict

import flask
from datetime import datetime

from blueprints.views.chores_board import ChoresBoardJsonView, ChoresBoardView, ChoresBoardSpecificView
from blueprints.views.dreams import DreamsRangeView, DreamsView
from blueprints.views.enrichment import EnrichmentView, EnrichmentFormView
from blueprints.views.fa_notifications import FANotificationsRangeView, FANotificationsView
from blueprints.views.mood import MoodRangeView, MoodView
from blueprints.views.mood_weekly import MoodWeeklyRangeView, MoodWeeklyView
from blueprints.views.named_dates import NamedDatesView
from blueprints.views.sleep_status import SleepStatusJsonView, SleepStatusView
from blueprints.views.sleep_time import SleepTimeRangeView, SleepTimeView
from blueprints.views.stats import StatsRangeView, StatsView
from data_source import DataSource
from decorators import view_auth_required
from blueprints.base_blueprint import BaseBlueprint


class ViewsBlueprint(BaseBlueprint):

    def __init__(self, data_source: DataSource, config: Dict[str, str]):
        super().__init__(data_source, "views")
        self.config = config

    def _list_views(self):
        return [
            SleepTimeRangeView(self.data_source, self.config),
            SleepTimeView(self.data_source, self.config),
            FANotificationsRangeView(self.data_source),
            FANotificationsView(self.data_source),
            MoodRangeView(self.data_source),
            MoodView(self.data_source),
            MoodWeeklyRangeView(self.data_source),
            MoodWeeklyView(self.data_source),
            SleepStatusJsonView(self.data_source, self.config),
            SleepStatusView(self.data_source, self.config),
            ChoresBoardJsonView(self.data_source),
            ChoresBoardView(self.data_source),
            ChoresBoardSpecificView(self.data_source),
            DreamsRangeView(self.data_source),
            DreamsView(self.data_source),
            NamedDatesView(self.data_source),
            EnrichmentView(self.data_source),
            EnrichmentFormView(self.data_source),
            StatsRangeView(self.data_source),
            StatsView(self.data_source)
        ]

    def register(self):
        self.blueprint.route("/")(self.list_views)
        for view in self._list_views():
            self.blueprint.add_url_rule(
                view.get_path(),
                f"{view.__class__.__name__}_call",
                view_auth_required(view.call)
            )

    @view_auth_required
    def list_views(self):
        views = [view.get_path() for view in self._list_views() if "<" not in view.get_path()]
        return flask.render_template("list_views.html", views=views)
