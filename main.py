from flask import Flask
app = Flask(__name__)


@app.route("/")
def hello_world():
    return "Hello, World!"


@app.route("/yo")
def yo_world():
    return "Yo, world, wassup?"


@app.route("/stats/")
def list_stats():
    return "A list of stats would live here."
