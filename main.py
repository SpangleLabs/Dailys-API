import json

import flask

from blueprints.forms import FormsBlueprint
from blueprints.stats import StatsBlueprint
from blueprints.views.blueprint import ViewsBlueprint
from data_source import FirestoreDataSource
from decorators import view_auth_required, get_auth_key
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


@app.route("/login")
def login_form():
    return flask.render_template("login_form.html")


@view_auth_required
@app.route("/login", methods=["POST"])
def login_submit():
    auth_key = get_auth_key("view_auth_key")
    resp = flask.make_response("Logged in")
    resp.set_cookie('view_auth_key', auth_key, max_age=86400*100)
    return resp


data_source = FirestoreDataSource()
stats_blueprint = StatsBlueprint(data_source)
stats_blueprint.register()
app.register_blueprint(stats_blueprint.blueprint, url_prefix="/stats")
views_blueprint = ViewsBlueprint(data_source, CONFIG)
views_blueprint.register()
app.register_blueprint(views_blueprint.blueprint, url_prefix="/views")
forms_blueprint = FormsBlueprint(data_source, CONFIG)
forms_blueprint.register()
app.register_blueprint(forms_blueprint.blueprint, url_prefix="/forms")

