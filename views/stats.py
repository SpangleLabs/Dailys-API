from datetime import datetime
from typing import Union

import flask
from flask import Blueprint, request, abort

from data_source import DataSource, CantUpdate
from decorators import edit_auth_required


class StatsBlueprint:

    def __init__(self, data_source: DataSource):
        self.DATA_SOURCE = data_source.data_source
        self.data_source = data_source
        self.blueprint = Blueprint("stats", __name__, template_folder='templates')

    def register(self):
        self.blueprint.route("/")(self.list_stats)
        self.blueprint.route("/<stat_name>/")(self.stat_data)
        self.blueprint.route("/<stat_name>/<view_date:view_date>/", methods=['GET'])(self.stat_data_on_date)
        self.blueprint.route("/<stat_name>/<view_date:view_date>/", methods=['PUT'])(self.update_stat_data_on_date)
        self.blueprint.route("/<stat_name>/<start_date:start_date>/<end_date:end_date>")(self.stat_data_with_date_range)

    def _get_unique_stat_names(self):
        unique_names = set()
        for stat in self.DATA_SOURCE.get():
            if stat.get("stat_name"):
                unique_names.add(stat.get("stat_name"))
        return unique_names

    def list_stats(self):
        return flask.jsonify(list(self._get_unique_stat_names()))

    def stat_data(self, stat_name: str):
        return flask.jsonify(self.data_source.get_stat_data(stat_name))

    def stat_data_on_date(self, stat_name: str, view_date: Union[datetime, str]):
        data = self.data_source.get_stat_for_date(stat_name, view_date)
        return flask.jsonify(data)

    @edit_auth_required
    def update_stat_data_on_date(self, stat_name: str, view_date: Union[datetime, str]):
        try:
            return flask.jsonify(
                self.data_source.set_stat_on_date(
                    stat_name,
                    view_date,
                    request.get_json(),
                    request.args.get("source")
                )
            )
        except CantUpdate:
            abort(404)

    def stat_data_with_date_range(self, stat_name, start_date, end_date):
        return flask.jsonify(self.data_source.get_stat_over_range(stat_name, start_date, end_date))
