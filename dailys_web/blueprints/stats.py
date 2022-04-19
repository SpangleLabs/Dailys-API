from datetime import datetime
from typing import Union

import flask
from flask import request, abort

from dailys_web.data_source.data_source import DataSource, CantUpdate
from dailys_web.decorators import edit_auth_required, view_auth_required
from dailys_web.blueprints.base_blueprint import BaseBlueprint


class StatsBlueprint(BaseBlueprint):

    def __init__(self, data_source: DataSource):
        super().__init__(data_source, "stats")

    def register(self):
        self.blueprint.route("/")(self.list_stats)
        self.blueprint.route("/<stat_name>/")(self.stat_data)
        self.blueprint.route("/<stat_name>/<view_date:view_date>/", methods=['GET'])(self.stat_data_on_date)
        self.blueprint.route("/<stat_name>/<view_date:view_date>/", methods=['PUT'])(self.update_stat_data_on_date)
        # self.blueprint.route("/stats/<stat_name>/<view_date:view_date>/", methods=['DELETE'],
        # self.remove_stat_data_on_date)
        self.blueprint.route("/<stat_name>/<start_date:start_date>/<end_date:end_date>")(self.stat_data_with_date_range)

    @view_auth_required
    def list_stats(self):
        return flask.jsonify(list(self.data_source.get_unique_stat_names()))

    @view_auth_required
    def stat_data(self, stat_name: str):
        return flask.jsonify(self.data_source.get_entries_for_stat(stat_name))

    @view_auth_required
    def stat_data_on_date(self, stat_name: str, view_date: Union[datetime, str]):
        data = self.data_source.get_entries_for_stat_on_date(stat_name, view_date)
        return flask.jsonify(data)

    @edit_auth_required
    def update_stat_data_on_date(self, stat_name: str, view_date: Union[datetime, str]):
        try:
            return flask.jsonify(
                self.data_source.update_entry_for_stat_on_date(
                    stat_name,
                    view_date,
                    request.get_json(),
                    request.args.get("source")
                )
            )
        except CantUpdate:
            abort(404)

    @view_auth_required
    def stat_data_with_date_range(self, stat_name, start_date, end_date):
        return flask.jsonify(self.data_source.get_entries_for_stat_over_range(stat_name, start_date, end_date))

    @edit_auth_required
    def remove_stat_data_on_date(self, stat_name, view_date):
        # See if data exists
        try:
            self.data_source.remove_stat_on_date(stat_name, view_date)
            return "Deleted"
        except KeyError:
            abort(404)
