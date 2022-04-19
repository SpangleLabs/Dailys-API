import json
from datetime import datetime

import flask

from dailys_web.blueprints.views.base_view import View
from dailys_web.path_converters import NAMED_DATES


class NamedDatesView(View):
    def get_path(self):
        return "/named_dates/"

    def call(self, **kwargs):
        return flask.render_template("named_dates.html", dates=NAMED_DATES)
