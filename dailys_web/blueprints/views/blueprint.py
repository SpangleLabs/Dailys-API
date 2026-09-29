import json
from typing import Dict

import flask
from datetime import datetime

from dailys_web.blueprints.views.chores_board import ChoresBoardJsonView, ChoresBoardView, ChoresBoardSpecificView
from dailys_web.blueprints.views.dreams import DreamsRangeView, DreamsView
from dailys_web.blueprints.views.enrichment import EnrichmentView, EnrichmentFormView
from dailys_web.blueprints.views.fa_notifications import FANotificationsRangeView, FANotificationsView
from dailys_web.blueprints.views.mood import MoodRangeView, MoodView
from dailys_web.blueprints.views.mood_weekly import MoodWeeklyRangeView, MoodWeeklyView
from dailys_web.blueprints.views.named_dates import NamedDatesView
from dailys_web.blueprints.views.question_each import IndividualQuestionRangeView, IndividualQuestionView
from dailys_web.blueprints.views.questions import QuestionsRangeView, QuestionsView
from dailys_web.blueprints.views.sleep_status import SleepStatusJsonView, SleepStatusView
from dailys_web.blueprints.views.sleep_time import SleepTimeRangeView, SleepTimeView
from dailys_web.blueprints.views.stats import StatsRangeView, StatsView
from dailys_web.data_source.data_source import DataSource
from dailys_web.decorators import view_auth_required
from dailys_web.blueprints.base_blueprint import BaseBlueprint


class ViewsListEntry:
    START_PLACEHOLDER = "<start_date:start_date>"
    END_PLACEHOLDER = "<end_date:end_date>"

    def __init__(self, view: View) -> None:
        self.view = view

    def _path_with_start_and_end(self, start_date: str, end_date: str) -> str:
        path = self.view.get_path()
        start_placeholder = self.START_PLACEHOLDER
        end_placeholder = self.END_PLACEHOLDER
        return path.replace(start_placeholder, start_date).replace(end_placeholder, end_date)

    def _last_year_path(self) -> str:
        today = datetime.date.today()
        last_year = today - datetime.timedelta(days=365)
        start_date = last_year.isoformat()
        end_date = "latest"
        return self._path_with_start_and_end(start_date, end_date)
    
    def _has_start_end_placeholders(self) -> bool:
        path = self.view.get_path()
        return self.START_PLACEHOLDER in path or self.END_PLACEHOLDER in path
    
    def _has_non_start_end_placeholders(self) -> bool:
        return "<" in self._path_with_start_and_end("", "")

    def full_path(self) -> str:
        if self._has_start_end_placeholders():
            return "/views/" + self._last_year_path()
        return "/views/" + self.view.get_path()

    def include_in_list(self) -> bool:
        return not self._has_non_start_end_placeholders()
    
    def display_text(self) -> str:
        if self._has_start_end_placeholders():
            clean_path = self._path_with_start_and_end("<start>", "<end>")
            return clean_path + " (Last 1 year)"
        return self.view.get_path()



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
            StatsView(self.data_source),
            QuestionsRangeView(self.data_source),
            QuestionsView(self.data_source),
            IndividualQuestionRangeView(self.data_source),
            IndividualQuestionView(self.data_source)
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
        view_entries = [ViewsListEntry(view) for view in self._list_views()]
        return flask.render_template("list_views.html", view_entries=view_entries)
