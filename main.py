import flask
import firebase_admin
from firebase_admin import firestore

from path_converters import DateConverter, EndDateConverter, SpecifiedDayConverter

app = flask.Flask(__name__)
app.url_map.converters['date'] = DateConverter
app.url_map.converters['end_date'] = EndDateConverter
app.url_map.converters['view_date'] = SpecifiedDayConverter

firebase_admin.initialize_app()
DATA_SOURCE = firestore.client().collection('Dailys stats')


@app.route("/")
def hello_world():
    return "Hello, World!"


@app.route("/yo")
def yo_world():
    return "Yo, world, wassup?"


@app.route("/stats/")
def list_stats():
    return "A list of stats would live here."


@app.route("/stats/<stat_name>/")
def stat_data(stat_name):
    return flask.jsonify([x.to_dict() for x in DATA_SOURCE.where("stat_name", "==", stat_name).get()])


@app.route("/stats/<stat_name>/<view_date:view_date>/")
def stat_data_on_date(stat_name, view_date):
    return "Data point for {} on the date {}.".format(
        stat_name,
        "today" if view_date == "latest" else (
            "[base data]" if view_date == "static" else view_date.isoformat()))


@app.route("/stats/<stat_name>/<date:start_date>/<end_date:end_date>")
def stat_data_with_date_range(stat_name, start_date, end_date):
    return "List of data for {} from {} to {}".format(
        stat_name,
        start_date.isoformat(),
        "today" if end_date == "latest" else end_date.isoformat())


@app.route("/example")
def example_firestore():
    return flask.jsonify(DATA_SOURCE.document('8WtthVhFgxx2vledo6H3').get().to_dict())
