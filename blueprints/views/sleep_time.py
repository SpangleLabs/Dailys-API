from datetime import timedelta

import flask
import numpy

from blueprints.views.base_view import View
from colour_scale import ColourScale, MidPointColourScale
from models import SleepData
from sleep_diary_image import SleepDiaryImage


class SleepTimeRangeView(View):

    def __init__(self, data_source):
        super().__init__(data_source)

    def get_path(self):
        return "/sleep_time/<start_date:start_date>/<end_date:end_date>/"

    def call(self, **kwargs):
        start_date = kwargs["start_date"]
        end_date = kwargs["end_date"]
        # Get data
        sleep_data_response = self.data_source.get_entries_for_stat_over_range("sleep", start_date, end_date)
        try:
            sleep_data = [SleepData(x) for x in sleep_data_response]
        except KeyError as e:
            return "Error while rendering sleep stats: {}".format(e), 500
        # Generate total stats
        stats = {}
        time_sleeping_list = [x.time_sleeping for x in sleep_data]
        stats['max'] = max(time_sleeping_list)
        stats['min'] = min(time_sleeping_list)
        # noinspection PyUnresolvedReferences
        stats['avg'] = timedelta(seconds=round(numpy.mean(time_sleeping_list).total_seconds()))
        stats['stdev'] = numpy.std([x.total_seconds() / 86400 for x in time_sleeping_list])
        stats['total'] = sum([x.total_seconds() / 86400 for x in time_sleeping_list])
        # Generate weekly stats
        weekly_stats = {}
        weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for day in [0, 1, 2, 3, 4, 5, 6, "weekday", "weekend"]:
            weekly_stats[day] = {}
            weekly_stats[day]['sleeps'] = []
            if isinstance(day, int):
                weekly_stats[day]['name'] = weekdays[day]
            else:
                weekly_stats[day]['name'] = day.title()
        for sleep_datum in sleep_data:
            weekday = (sleep_datum.date.weekday() + 1) % 7
            weekly_stats[weekday]['sleeps'].append(sleep_datum.time_sleeping.total_seconds())
            if weekday in [5, 6]:
                weekly_stats["weekend"]['sleeps'].append(sleep_datum.time_sleeping.total_seconds())
            else:
                weekly_stats['weekday']['sleeps'].append(sleep_datum.time_sleeping.total_seconds())
        for day in weekly_stats.keys():
            if len(weekly_stats[day]['sleeps']) == 0:
                weekly_stats[day]['avg'] = None
            else:
                # noinspection PyTypeChecker
                weekly_stats[day]['avg'] = timedelta(seconds=round(numpy.mean(weekly_stats[day]['sleeps'])))
        # Create scales
        stats_scale = MidPointColourScale(
            stats['min'], stats['avg'], stats['max'],
            ColourScale.YELLOW, ColourScale.WHITE, ColourScale.GREEN
        )
        weekly_scale = MidPointColourScale(
            min([x['avg'] for x in weekly_stats.values() if x['avg'] is not None]),
            stats['avg'],
            max([x['avg'] for x in weekly_stats.values() if x['avg'] is not None]),
            ColourScale.YELLOW, ColourScale.WHITE, ColourScale.GREEN
        )
        # Generate images
        images = dict()
        for sleep in sleep_data:
            image = SleepDiaryImage()
            image.add_sleep_data(sleep)
            images[sleep.date] = image.to_base64_encoded()
        # Return page
        return flask.render_template(
            "sleep_time.html",
            sleeps=sleep_data,
            stats=stats,
            weekly_stats=weekly_stats,
            stats_scale=stats_scale,
            weekly_scale=weekly_scale,
            sleep_images=images
        )


class SleepTimeView(SleepTimeRangeView):

    def get_path(self):
        return "/sleep_time/"

    def call(self, **kwargs):
        return super().call(start_date="earliest", end_date="latest")
