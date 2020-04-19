import json
from typing import Dict

import flask as flask
from data_source import DataSource
from flask import abort, request, redirect

from decorators import edit_auth_required, view_auth_required
from blueprints.base_blueprint import BaseBlueprint
from models.dream_night import DreamNight
from models.fa_data import FuraffinityData
from models.sleep_data import SleepData


class FormsBlueprint(BaseBlueprint):

    def __init__(self, data_source: DataSource, config: Dict[str, str]):
        super().__init__(data_source, "forms")
        self.config = config

    def register(self):
        self.blueprint.route("/")(self.list_forms)
        self.blueprint.route(
            "/raw/<stat_name>/<view_date:view_date>/", methods=['GET']
        )(self.raw_form)
        self.blueprint.route(
            "/raw/<stat_name>/<view_date:view_date>/", methods=['POST']
        )(self.raw_form_post)
        self.blueprint.route(
            "/chores_done/<view_date:view_date>/", methods=['POST']
        )(self.chores_form_post)
        self.blueprint.route(
            "/enrichment/<stat_name>/<view_date:view_date>/", methods=["POST"]
        )(self.enrich_data)

    @view_auth_required
    def list_forms(self):
        forms = ["raw"]
        return flask.render_template("list_forms.html", forms=forms)

    @view_auth_required
    def raw_form(self, stat_name, view_date):
        raw_entries = self.data_source.get_entries_for_stat_on_date(stat_name, view_date)
        if raw_entries:
            data = raw_entries[0]["data"]
        else:
            data = None
        raw_data = json.dumps(data, indent=2, sort_keys=True)
        return flask.render_template(
            "form_raw.html",
            stat_name=stat_name, view_date=view_date, raw_data=raw_data
        )

    @edit_auth_required
    def raw_form_post(self, stat_name, view_date):
        new_data = json.loads(request.form['new_data'])
        self.data_source.update_entry_for_stat_on_date(
            stat_name,
            view_date,
            new_data,
            "Updated via dailys form"
        )
        # Get data and return the form
        return self.raw_form(stat_name, view_date)

    @edit_auth_required
    def chores_form_post(self, view_date):
        chore = request.form['chore']
        board_name = request.form['board_name']
        current_data = self.data_source.get_entries_for_stat_on_date("chores", view_date)
        if len(current_data) == 0:
            new_data = dict()
        else:
            new_data = current_data[0]['data']
        if "chores_done" not in new_data:
            new_data['chores_done'] = []
        if chore in new_data['chores_done']:
            new_data['chores_done'].remove(chore)
        else:
            new_data['chores_done'].append(chore)
        self.data_source.update_entry_for_stat_on_date(
            "chores",
            view_date,
            new_data,
            "Updated via chores board"
        )
        board_path = f"/views/chores_board/{board_name or ''}/"
        return redirect(board_path, code=302)

    @edit_auth_required
    def enrich_data(self, stat_name, view_date):
        model_classes = {
            "sleep": SleepData,
            "duolingo": None,
            "chores": None,
            "furaffinity": FuraffinityData,
            "dreams": DreamNight,
            "mood": None
        }
        entries = self.data_source.get_entries_for_stat_on_date(stat_name, view_date)
        model_class = model_classes.get(stat_name)
        model = model_class(entries[0])
        new_data = model.enriched_data(request.form)
        self.data_source.update_entry_for_stat_on_date(stat_name, view_date, new_data, model.source)
        print(new_data)
        print(request.form)
        return "Enrichment"
