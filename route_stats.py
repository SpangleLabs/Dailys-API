import flask
from flask import Blueprint

blueprint = Blueprint("stats", __name__, template_folder='templates')


def init(data):
    global DATA_SOURCE
    DATA_SOURCE = data


def get_unique_stat_names():
    unique_names = set()
    for stat in DATA_SOURCE.get():
        if stat.get("stat_name"):
            unique_names.add(stat.get("stat_name"))
    return unique_names


@blueprint.route("/")
def list_stats():
    return flask.jsonify(list(get_unique_stat_names()))


@blueprint.route("/<stat_name>/")
def stat_data(stat_name):
    return flask.jsonify([x.to_dict() for x in DATA_SOURCE.where("stat_name", "==", stat_name).order_by("date").get()])
