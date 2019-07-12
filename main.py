import json

import flask

from data_source import DataSource
from views import stats, views
from path_converters import DateConverter, EndDateConverter, SpecifiedDayConverter, StartDateConverter

# Load converters
app = flask.Flask(__name__)
app.url_map.converters['date'] = DateConverter
app.url_map.converters['start_date'] = StartDateConverter
app.url_map.converters['end_date'] = EndDateConverter
app.url_map.converters['view_date'] = SpecifiedDayConverter

with open("config.json", "r") as f:
    CONFIG = json.load(f)


@app.route("/")
def hello_world():
    return "Hello, World! This is Spangle's dailys recording system."


data_source = DataSource()
stats_blueprint = stats.StatsBlueprint(data_source)
stats_blueprint.register()
app.register_blueprint(stats_blueprint.blueprint, url_prefix="/stats")
views_blueprint = views.ViewsBlueprint(data_source, CONFIG)
views_blueprint.register()
app.register_blueprint(views_blueprint.blueprint, url_prefix="/views")
