from datetime import time, datetime, timedelta

import flask
import firebase_admin
from firebase_admin import firestore

from flask import request

from models import SleepData
from path_converters import DateConverter, EndDateConverter, SpecifiedDayConverter, StartDateConverter

app = flask.Flask(__name__)
app.url_map.converters['date'] = DateConverter
app.url_map.converters['start_date'] = StartDateConverter
app.url_map.converters['end_date'] = EndDateConverter
app.url_map.converters['view_date'] = SpecifiedDayConverter

firebase_admin.initialize_app()
DATA_SOURCE = firestore.client().collection('Dailys stats')


@app.route("/")
def hello_world():
    return "Hello, World! This is Spangle's dailys recording system."


def get_unique_stat_names():
    unique_names = set()
    for stat in DATA_SOURCE.get():
        if stat.get("stat_name"):
            unique_names.add(stat.get("stat_name"))
    return unique_names


@app.route("/stats/")
def list_stats():
    return flask.jsonify(list(get_unique_stat_names()))


@app.route("/stats/<stat_name>/")
def stat_data(stat_name):
    return flask.jsonify([x.to_dict() for x in DATA_SOURCE.where("stat_name", "==", stat_name).order_by("date").get()])


def get_stat_for_date(stat_name, view_date):
    data_partial = DATA_SOURCE.where("stat_name", "==", stat_name)
    if view_date == "latest":
        data_partial = data_partial.order_by("date").limit(1)
    elif view_date == "static":
        data_partial = data_partial.where("date", "==", "static")
    else:
        start_datetime = datetime.combine(view_date, time(0, 0, 0))
        end_datetime = datetime.combine(view_date + timedelta(days=1), time(0, 0, 0))
        data_partial = data_partial.where("date", ">=", start_datetime).where("date", "<", end_datetime)
    return list(data_partial.get())


@app.route("/stats/<stat_name>/<view_date:view_date>/", methods=['GET'])
def stat_data_on_date(stat_name, view_date):
    data = get_stat_for_date(stat_name, view_date)
    return flask.jsonify([x.to_dict() for x in data])


@app.route("/stats/<stat_name>/<view_date:view_date>/", methods=['PUT'])
def update_stat_data_on_date(stat_name, view_date):
    # Construct new data object
    new_data = request.get_json()
    total_data = {'stat_name': stat_name}
    if view_date == "latest":
        raise Exception("Not sure how to best handle this.")  # TODO
    elif view_date == "static":
        total_data['date'] = "static"
    else:
        total_data['date'] = datetime.combine(view_date, time(0, 0, 0))
    total_data['source'] = request.args.get("source", "Unknown [via API]")
    total_data['data'] = new_data
    # See if data exists
    data = get_stat_for_date(stat_name, view_date)
    if len(data) == 1:
        DATA_SOURCE.document(data[0].id).set(total_data)
    else:
        DATA_SOURCE.add(total_data)
    return flask.jsonify(total_data)


@app.route("/stats/<stat_name>/<start_date:start_date>/<end_date:end_date>")
def stat_data_with_date_range(stat_name, start_date, end_date):
    data_partial = DATA_SOURCE.where("stat_name", "==", stat_name)
    # Filter start date
    if start_date != "earliest":
        start_datetime = datetime.combine(start_date, time(0, 0, 0))
        data_partial = data_partial.where("date", ">=", start_datetime)
    # Filter end date
    if end_date != "latest":
        end_datetime = datetime.combine(end_date + timedelta(days=1), time(0, 0, 0))
        data_partial = data_partial.where("date", "<=", end_datetime)
    # Collapse data to dicts
    data = [x.to_dict() for x in data_partial.order_by("date").get()]
    # If date range is unbounded, filter out static data
    if start_date == "earliest" and end_date == "latest":
        data = [x for x in data if x['date'] != 'static']
    return flask.jsonify(data)


@app.route("/views/")
def list_views():
    views = ["sleep_time"]
    return flask.render_template("list_views.html", views=views)


@app.route("/views/sleep_time/<start_date:start_date>/<end_date:end_date>")
def view_sleep_stats_range(start_date, end_date):
    sleep_data_response = stat_data_with_date_range("sleep", start_date, end_date)
    sleep_data = [SleepData(x) for x in sleep_data_response.get_json() if x['date'] != "static"]
    return flask.render_template("sleep_time.html", sleeps=sleep_data)


@app.route("/views/sleep_time/")
def view_sleep_stats():
    return view_sleep_stats_range("earliest", "latest")
