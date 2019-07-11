import flask
from flask import Blueprint


class StatsBlueprint:

    def __init__(self, data_source):
        self.DATA_SOURCE = data_source
        self.blueprint = Blueprint("stats", __name__, template_folder='templates')

    def register(self):
        self.blueprint.route("/")(self.list_stats)
        self.blueprint.route("/<stat_name>/")(self.stat_data)

    def get_unique_stat_names(self):
        unique_names = set()
        for stat in self.DATA_SOURCE.get():
            if stat.get("stat_name"):
                unique_names.add(stat.get("stat_name"))
        return unique_names

    def list_stats(self):
        return flask.jsonify(list(self.get_unique_stat_names()))

    def stat_data(self, stat_name):
        return flask.jsonify(
            [
                x.to_dict()
                for x
                in self.DATA_SOURCE.where("stat_name", "==", stat_name).order_by("date").get()
            ]
        )
