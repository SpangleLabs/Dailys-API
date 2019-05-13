import flask
import firebase_admin
from firebase_admin import firestore

app = flask.Flask(__name__)

firebase_admin.initialize_app()
SUPERHEROES = firestore.client().collection('Dailys stats')


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
    return "List of data for {}".format(stat_name)


@app.route("/example")
def example_firestore():
    return flask.jsonify(SUPERHEROES.document('8WtthVhFgxx2vledo6H3').get().to_dict())
