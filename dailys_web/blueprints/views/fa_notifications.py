from datetime import timedelta

import flask

from dailys_web.blueprints.views.base_view import View
from dailys_web.colour_scale import ColourScale
from dailys_models.fa_data import FuraffinityData
from dailys_web.nav_data import NavData


class FANotificationsRangeView(View):

    def get_path(self):
        return "/fa_notifications/<start_date:start_date>/<end_date:end_date>/"

    def call(self, **kwargs):
        start_date = kwargs["start_date"]
        end_date = kwargs["end_date"]
        # Get data
        fa_data_response = self.data_source.get_entries_for_stat_over_range("furaffinity", start_date, end_date)
        fa_data = {
            FuraffinityData(x).date: {"data": FuraffinityData(x)}
            for x in fa_data_response
        }
        # Add in diff data
        for today in fa_data.keys():
            yesterday = today - timedelta(days=1)
            fa_data[today]['diff'] = None
            if yesterday in fa_data:
                diff = fa_data[today]['data'].total - fa_data[yesterday]['data'].total
                if diff >= 0:
                    fa_data[today]['diff'] = diff
        # Create colour scale
        max_notif = max([x['data'].total for x in fa_data.values()])
        scale = ColourScale(0, max_notif, ColourScale.WHITE, ColourScale.RED)
        # Render template
        return flask.render_template("fa_notifications.html", nav_data=NavData(), fa_notifications=fa_data, scale=scale)


class FANotificationsView(FANotificationsRangeView):

    def get_path(self):
        return "/fa_notifications/"

    def call(self, **kwargs):
        return super().call(start_date="earliest", end_date="latest")
