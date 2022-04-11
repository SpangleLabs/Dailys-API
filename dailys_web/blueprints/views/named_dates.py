import json
from datetime import datetime

import flask

from dailys_web.blueprints.views.base_view import View


class NamedDatesView(View):
    def get_path(self):
        return "/named_dates/"

    def call(self, **kwargs):
        with open("named-dates.json", "r") as f:
            data = json.load(f)
            named_dates = {k: datetime.strptime(v, '%Y-%m-%d').date() for k, v in data.items()}
        return flask.render_template("named_dates.html", dates=named_dates)
