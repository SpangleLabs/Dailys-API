from datetime import timedelta

import flask

from dailys_web.blueprints.views.base_view import View
from dailys_web.colour_scale import ColourScale
from dailys_models.mood_measurement import MoodMeasurement
from dailys_models.sleep_data import SleepData


class MoodRangeView(View):

    def get_path(self):
        return "/mood/<start_date:start_date>/<end_date:end_date>/"

    def call(self, **kwargs):
        start_date = kwargs["start_date"]
        end_date = kwargs["end_date"]
        # Get static mood data
        mood_static = self.data_source.get_entries_for_stat_on_date("mood", "static")[0]['data']
        # Get mood data
        mood_data = self.data_source.get_entries_for_stat_over_range("mood", start_date, end_date)
        # Get sleep data, if necessary
        sleep_data = {}
        if "WakeUpTime" in mood_static['times'] or "SleepTime" in mood_static['times']:
            sleep_start_date = start_date
            if start_date != "earliest":
                sleep_start_date -= timedelta(days=1)
            sleep_end_date = end_date
            if end_date != "latest":
                sleep_end_date -= timedelta(days=1)
            sleep_data_response = self.data_source.get_entries_for_stat_over_range("sleep", sleep_start_date, sleep_end_date)
            sleep_data = {SleepData(x).date: SleepData(x) for x in sleep_data_response}
        # Create list of mood measurements
        mood_measurements = [
            MoodMeasurement(x, mood_time, sleep_data)
            for x in mood_data
            for mood_time in mood_static['times']
            if mood_time in x['data']
        ]
        # Create scales
        scale = ColourScale(1, 5, ColourScale.WHITE, ColourScale.DANDELION)
        # TODO: define what mood measurements are good vs bad
        scale_good = ColourScale(1, 5, ColourScale.WHITE, ColourScale.GREEN)
        scale_bad = ColourScale(1, 5, ColourScale.WHITE, ColourScale.RED)
        # Render template
        return flask.render_template(
            "mood.html",
            mood_static=mood_static,
            mood_measurements=mood_measurements,
            scale=scale,
            scale_good=scale_good,
            scale_bad=scale_bad
        )


class MoodView(MoodRangeView):

    def get_path(self):
        return "/mood/"

    def call(self, **kwargs):
        return super().call(start_date="earliest", end_date="latest")
