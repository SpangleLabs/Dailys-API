from typing import Dict

import flask as flask
from data_source import DataSource
from flask import abort
from views.base_blueprint import BaseBlueprint


class FormsBlueprint(BaseBlueprint):

    def __init__(self, data_source: DataSource, config: Dict[str, str]):
        super().__init__(data_source, "views")
        self.config = config

    def register(self):
        self.blueprint.route("/")(self.list_forms)
        self.blueprint.route(
            "/raw/<stat_name>/<view_date:view_date>/", methods=['GET']
        )(self.raw_form)
        self.blueprint.route(
            "/raw/<stat_name>/<view_date:view_date>/", methods=['POST']
        )(self.raw_form_post)

    def list_forms(self):
        forms = ["raw"]
        return flask.render_template("list_forms.html", forms=forms)

    def raw_form(self, stat_name, view_date):
        raw_data = self.data_source.get_entries_for_stat_on_date(stat_name, view_date)
        return flask.render_template(
            "form_raw.html",
            stat_name=stat_name, view_date=view_date, raw_data=raw_data
        )

    def raw_form_post(self, stat_name, view_date):
        auth_key = ""  # TODO
        new_data = ""  # TODO
        if auth_key != "todo":  # TODO
            abort(401)  # TODO: use decorator's method, somehow
        self.data_source.update_entry_for_stat_on_date(
            stat_name,
            view_date,
            new_data,
            "Updated via dailys form"
        )
        raw_data = self.data_source.get_entries_for_stat_on_date(stat_name, view_date)
        return flask.render_template(
            "form_raw.html",
            stat_name=stat_name, view_date=view_date, raw_data=raw_data
        )
